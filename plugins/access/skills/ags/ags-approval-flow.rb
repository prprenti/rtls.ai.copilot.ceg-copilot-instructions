#!/usr/bin/env ruby
# ------------------------------------------------------------------------------
# ags-approval-flow.rb - AGS Approval Workflow Automation
# 
# This script automates the AGS approval process based on badge type, 
# organization, and justification content.
#
# Usage:
#   ags-approval-flow.rb [--dry-run] [--output FILE]
#
# Options:
#   --dry-run       Show what would be done without executing approvals
#   --output FILE   Output script file (default: approvals.sh)
#   --approver USER Override approver (default: current user)
#   -h, --help      Show this help message
#
# Approval Rules:
#   1. GB badge + "Justified through SAAF" in justification → Auto-approve
#   2. BB badge + OrgUnitDescr contains "CSiG DDG" → Auto-approve
#   3. BB badge + NOT "CSiG DDG" + name/idsid/wwid in justification → Script (uncommented approve)
#   4. BB badge + NOT "CSiG DDG" + NO name/idsid/wwid → Script (commented approve)
#   5. No match → Listed in table at bottom of script
# ------------------------------------------------------------------------------

require 'optparse'
require 'json'
require 'set'

# Configuration
CDISLOOKUP_PATH = File.expand_path('../employee-lookup/employee_lookup.py', __FILE__)

options = {
  dry_run: false,
  output: 'approvals.sh',
  approver: ENV['USER']
}

parser = OptionParser.new do |opts|
  opts.banner = "Usage: #{$PROGRAM_NAME} [options]"
  opts.separator ""
  opts.separator "Options:"

  opts.on("--dry-run", "Show what would be done without executing approvals") do
    options[:dry_run] = true
  end

  opts.on("--output FILE", "Output script file (default: approvals.sh)") do |file|
    options[:output] = file
  end

  opts.on("--approver USER", "Override approver (default: current user)") do |user|
    options[:approver] = user
  end

  opts.on("-h", "--help", "Show this help message") do
    puts opts
    puts ""
    puts "Approval Rules:"
    puts "  1. GB badge + 'Justified through SAAF' in justification → Auto-approve"
    puts "  2. BB badge + OrgUnitDescr contains 'CSiG DDG' → Auto-approve"
    puts "  3. BB badge + NOT 'CSiG DDG' + name/idsid/wwid in justification → Script (uncommented)"
    puts "  4. BB badge + NOT 'CSiG DDG' + NO identifier found → Script (commented)"
    puts "  5. No match → Listed in table at bottom of script"
    exit 0
  end
end

parser.parse!

# Cache for CDIS lookups to avoid repeated calls
$cdis_cache = {}

def lookup_cdis(idsid)
  return $cdis_cache[idsid] if $cdis_cache.key?(idsid)
  
  # Use the employee_lookup.py script or fall back to system cdislookup
  if File.exist?(CDISLOOKUP_PATH)
    output = `python3 #{CDISLOOKUP_PATH} -u #{idsid} -k IDSID,WWID,BookName,OrgUnitDescr -f json 2>/dev/null`
  else
    # Fallback to parsing raw cdislookup output
    output = `/usr/intel/bin/cdislookup -i #{idsid} 2>/dev/null`
    if output && !output.include?('No matches')
      data = {}
      output.split("\n").each do |line|
        parts = line.split("=", 2)
        next unless parts.length == 2
        data[parts[0].strip] = parts[1].strip
      end
      $cdis_cache[idsid] = data
      return data
    end
    $cdis_cache[idsid] = nil
    return nil
  end
  
  begin
    result = JSON.parse(output)
    $cdis_cache[idsid] = result.is_a?(Array) ? result.first : result
  rescue JSON::ParserError
    $cdis_cache[idsid] = nil
  end
  
  $cdis_cache[idsid]
end

def extract_identifiers_from_justification(justification)
  return { found: false, identifiers: [] } if justification.nil? || justification.empty?
  
  identifiers = []
  
  # Look for explicit WWID patterns: "wwid=10630385", "wwid = 10630385", "wwid:10630385"
  wwid_patterns = justification.scan(/wwid\s*[=:]\s*(\d+)/i)
  wwid_patterns.each do |match|
    wwid = match[0]
    cdis = lookup_cdis(wwid)
    if cdis && cdis['IDSID']
      identifiers << { type: 'WWID', value: wwid, name: cdis['BookName'], idsid: cdis['IDSID'] }
    end
  end
  
  # Look for explicit IDSID/userid patterns: "userid=geruhl", "idsid = jsmith", "userid: abc123"
  idsid_patterns = justification.scan(/(?:userid|idsid|sponsor)\s*[=:]\s*([a-z][a-z0-9]+)/i)
  idsid_patterns.each do |match|
    idsid = match[0].downcase
    cdis = lookup_cdis(idsid)
    if cdis && cdis['IDSID']
      unless identifiers.any? { |i| i[:idsid]&.downcase == cdis['IDSID'].downcase }
        identifiers << { type: 'IDSID', value: idsid, name: cdis['BookName'], idsid: cdis['IDSID'] }
      end
    end
  end
  
  # Look for sponsor patterns: "sponsor is Pouria", "sponsor = jsmith", "sponsor: geruhl"
  # Sponsor can be a name (first name) or an IDSID
  sponsor_patterns = justification.scan(/sponsor\s*(?:is|[=:])\s*([a-z][a-z0-9]*)/i)
  sponsor_patterns.each do |match|
    sponsor = match[0].downcase
    cdis = lookup_cdis(sponsor)
    if cdis && cdis['IDSID']
      unless identifiers.any? { |i| i[:idsid]&.downcase == cdis['IDSID'].downcase }
        identifiers << { type: 'Sponsor', value: sponsor, name: cdis['BookName'], idsid: cdis['IDSID'] }
      end
    end
  end
  
  { found: !identifiers.empty?, identifiers: identifiers }
end

def is_csig_ddg?(idsid)
  cdis = lookup_cdis(idsid)
  return false unless cdis
  
  org = cdis['OrgUnitDescr'] || ''
  org.include?('CSiG DDG')
end

# Fetch pending approvals
puts "Fetching pending approvals for #{options[:approver]}..."
cmd = "ags status --approver #{options[:approver]} -fo json -fi 'Requestee,Requestee_badgetype,Work Item ID,Requested Entitlement/Role,Justification'"
json_output = `#{cmd} 2>/dev/null`

begin
  requests = JSON.parse(json_output)
rescue JSON::ParserError => e
  warn "Error parsing AGS output: #{e.message}"
  warn "Raw output: #{json_output[0..500]}"
  exit 1
end

if requests.empty?
  puts "No pending approvals found."
  exit 0
end

puts "Found #{requests.length} pending request(s)."

# Categorize requests
auto_approve = []      # Will be approved immediately
script_approve = []    # Will be written to script (uncommented)
script_review = []     # Will be written to script (commented - needs review)
unmatched = []         # Will be listed in table

requests.each do |req|
  requestee = req['Requestee'] || req['requestee']
  badge_type = (req['requestee_badgeType'] || req['Requestee_badgetype'] || req['Requestee_badgeType'] || '').upcase
  work_item_id = req['Work Item ID'] || req['work_item_id'] || req['workItemId']
  role_name = req['Requested Entitlement/Role'] || req['requested_entitlement_role'] || req['entityName']
  justification = req['Justification'] || req['justification'] || ''
  
  item = {
    requestee: requestee,
    badge_type: badge_type,
    work_item_id: work_item_id,
    role_name: role_name,
    justification: justification
  }
  
  if badge_type == 'GB'
    # Rule 1: GB + "Justified through SAAF"
    if justification.downcase.include?('justified through saaf')
      item[:reason] = "GB badge with SAAF justification"
      auto_approve << item
    else
      item[:reason] = "GB badge without SAAF justification - needs review"
      unmatched << item
    end
  elsif badge_type == 'BB'
    # Check org unit
    if is_csig_ddg?(requestee)
      # Rule 2: BB + CSiG DDG org
      item[:reason] = "BB badge in CSiG DDG organization"
      auto_approve << item
    else
      # Rules 3 & 4: BB + NOT CSiG DDG - check for identifiers
      id_result = extract_identifiers_from_justification(justification)
      if id_result[:found]
        item[:reason] = "BB badge outside CSiG DDG - identifier found in justification"
        item[:identifiers] = id_result[:identifiers]
        script_approve << item
      else
        item[:reason] = "BB badge outside CSiG DDG - NO identifier found in justification"
        script_review << item
      end
    end
  else
    # Unknown badge type
    item[:reason] = "Unknown badge type: #{badge_type}"
    unmatched << item
  end
end

# Report summary
puts "\n" + "=" * 60
puts "APPROVAL WORKFLOW SUMMARY"
puts "=" * 60
puts "Auto-approve (immediate):     #{auto_approve.length}"
puts "Script approve (uncommented): #{script_approve.length}"
puts "Script review (commented):    #{script_review.length}"
puts "Unmatched (needs review):     #{unmatched.length}"
puts "=" * 60

# Execute auto-approvals
unless auto_approve.empty?
  puts "\n--- AUTO-APPROVING #{auto_approve.length} REQUEST(S) ---"
  auto_approve.each do |item|
    puts "  #{item[:requestee]} -> #{item[:role_name]} (#{item[:reason]})"
    unless options[:dry_run]
      system("ags approve --id #{item[:work_item_id]}")
    end
  end
end

# Generate approvals.sh script
script_content = []
script_content << "#!/bin/bash"
script_content << "# AGS Approval Script - Generated #{Time.now.strftime('%Y-%m-%d %H:%M:%S')}"
script_content << "# Approver: #{options[:approver]}"
script_content << "#"
script_content << "# Review the commands below and execute this script to process approvals."
script_content << "# Uncommented 'ags approve' commands will be executed."
script_content << "# Uncommented 'ags deny' commands will be executed."
script_content << ""

# Script approve items (identifier found - uncommented approve)
unless script_approve.empty?
  script_content << "# " + "=" * 58
  script_content << "# APPROVE - Identifier found in justification (BB non-CSiG DDG)"
  script_content << "# " + "=" * 58
  script_content << ""
  
  script_approve.each do |item|
    id_info = item[:identifiers].map { |i| "#{i[:type]}=#{i[:value]} (#{i[:name]})" }.join(", ")
    script_content << "# Requestee: #{item[:requestee]} | Role: #{item[:role_name]}"
    script_content << "# Found: #{id_info}"
    script_content << "# Justification: #{item[:justification][0..100]}#{'...' if item[:justification].length > 100}"
    script_content << "ags approve --id #{item[:work_item_id]}"
    script_content << "# ags deny --id #{item[:work_item_id]} --comment \"Denied - requires additional justification\""
    script_content << ""
  end
end

# Script review items (no identifier found - commented approve)
unless script_review.empty?
  script_content << "# " + "=" * 58
  script_content << "# REVIEW REQUIRED - No identifier found (BB non-CSiG DDG)"
  script_content << "# " + "=" * 58
  script_content << ""
  
  script_review.each do |item|
    script_content << "# Requestee: #{item[:requestee]} | Role: #{item[:role_name]}"
    script_content << "# Justification: #{item[:justification][0..100]}#{'...' if item[:justification].length > 100}"
    script_content << "# NO identifier (name/idsid/wwid) found in justification"
    script_content << "# ags approve --id #{item[:work_item_id]}"
    script_content << "ags deny --id #{item[:work_item_id]} --comment \"All Non-DDG employees should onboard from their own orgs.  If the requestee is working as a loaner to DDG, then please provide a sponsor idsid, wwid, or name in the SAAF justification field.  Modify the existing subscription, update the justificaiton, and resubmit.\""
    script_content << ""
  end
end

# Unmatched items (table at bottom)
unless unmatched.empty?
  script_content << "# " + "=" * 58
  script_content << "# UNMATCHED - Requires manual review"
  script_content << "# " + "=" * 58
  script_content << "#"
  script_content << "# | Requestee   | Badge | Work Item ID | Role                              | Reason"
  script_content << "# |-------------|-------|--------------|-----------------------------------|----------------------------------"
  
  unmatched.each do |item|
    script_content << "# | #{item[:requestee].to_s.ljust(11)} | #{item[:badge_type].to_s.ljust(5)} | #{item[:work_item_id].to_s.ljust(12)} | #{item[:role_name].to_s[0..32].ljust(33)} | #{item[:reason]}"
  end
  
  script_content << "#"
  script_content << "# Justifications:"
  unmatched.each do |item|
    script_content << "# #{item[:requestee]}: #{item[:justification][0..120]}#{'...' if item[:justification].to_s.length > 120}"
  end
  script_content << ""
end

# Write script file if there's content beyond the header
if script_approve.any? || script_review.any? || unmatched.any?
  File.write(options[:output], script_content.join("\n"))
  File.chmod(0755, options[:output])
  puts "\nGenerated: #{options[:output]}"
  puts "  - #{script_approve.length} approve commands (uncommented)"
  puts "  - #{script_review.length} deny commands (uncommented, approve commented)"
  puts "  - #{unmatched.length} items in review table"
  puts "\nReview and run: ./#{options[:output]}"
else
  puts "\nNo script generated (all items were auto-approved or list is empty)."
end

if options[:dry_run]
  puts "\n[DRY RUN] No approvals were executed. Remove --dry-run to execute."
end
