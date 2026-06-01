QUERY_TOOL = create_list_file
LIST_TEMPLATES ?= hubs.hip noreuse.sip hubs.sip val/vip val/noreuse.vip

ifeq ($(IPHANDOFF_EXEC),)
   export IPHANDOFF_EXEC := $(shell cth_query -tool $(QUERY_TOOL) PARAMS create_list_file_exec -resolve -q)
endif

ifeq ($(IPHANDOFF_DIR),)
   export IPHANDOFF_DIR := $(shell cth_query -tool $(QUERY_TOOL) PARAMS create_list_file_path -resolve -q)
endif
export PATH := /p/ipx/cad/ipxclient/prod/ph3:$(PATH)

all: $(addsuffix .ipx,$(LIST_TEMPLATES))

prep_dirs:
	@mkdir -p $(WORKAREA)/output/fbi/

define MAKE_LIST_FILE
$1.ipx: prep_dirs
	@filename=$$$$(echo $1 | sed 's@/@.@g' ); \
	printf "Processing $1.ipx to generate $1.list\n\tlog_file= $(WORKAREA)/output/fbi/create_list_file.$$$${filename}.log\n\n"; \
	start=$$$$(date +%s); \
	$(IPHANDOFF_EXEC) -input $(WORKAREA)/filelists/$1.ipx -output $(WORKAREA)/filelists/$1.list -config $(WORKAREA)/integration/create_list_file/config_ttl.ini -logdir $(WORKAREA)/output/fbi -logname :module:/:item:_:time:.log ; \
	exit_status=$$$$?; \
	end=$$$$(date +%s); \
	printf "Done processing $1.ipx to generate $1.list\n\tExit Status:$$$$((exit_status))\
	\n\tElapsed time: %s seconds\n\n" $$$$((end-start)); \
	exit $$$$((exit_status))
endef

$(foreach ltemp,$(LIST_TEMPLATES),$(eval $(call MAKE_LIST_FILE,$(ltemp))))
