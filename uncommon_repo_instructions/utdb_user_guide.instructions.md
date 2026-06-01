---
applyTo: "src/val/griffin**,src/val/utdb,**/*griffin*.prompt.md"
---




**Table of Content**
[TOC levels=1,2]

_________________________________________________________________________________________________________________________________________________________________________________________________________
# 1. Introduction
Validation tasks involve many activities like defining the test content, developing the tests, executing the tests and analyzing the test results. Some of the test result analysis occurs during tests execution as part of the test code. Other result analysis occurs after the test run as part of post-processing activities. The post-processing relies on test output information that is generated as part of the test execution such as text logs, Jem trace, etc. It can be used for multiple purposes such as debugging, checking correctness, collecting coverage, bucketing failures and more. The Unified Transactions Database (UTDB) tool provides capabilities to store and access test result data via Python AI for all these kinds of activities. This document provides information about these capabilities and how they can be used.

## 1.1 Overview
Test result data may come in a variety of forms, among them:

+ ***Structured textual logs:***

> Such logs may be uploaded into UTDB storage and be accessed and analyzed using the UTDB Python API. The basic structure of the storage resembles relational database tables. A table has many records; each record is comprised of fields; fields store values of certain data type (integers, strings, etc.). A record typically represents some information that was taken from one of the tests output logs.


+ ***Unstructured textual logs:***

> Unstructured logs require a more involved process of structuring them into a tabular form first. Certain capabilities to ease this process are available, but it's possible to use a completely custom mechanism of structuring the data as part of the uploading process.


+ ***Jem traces:***

> Jem traces may be accessed and analyzed directly via UTDB Python API. (Currently there are certain limitations on usage of some of the capabilities on Jem traces; they are being gradually removed.) Noteworthy, values in Jem traces are different from those coming from textual logs in the fact that they closely resemble SystemVerilog data types, including 4-value support, enums, packed aggregate types, etc.

> Alternatively, a conversion process using any of the standard Jem post-processing methods is possible.  For example, Jem-Python post-processing method allows interpreting the raw trace data and storing the results directly into UTDB.  

Once the test result data is available in the UTDB, it can be analyzed in many different ways. The analysis is basically done by querying UTDB and analyzing the results of the query. The query capabilities are quite extensive and together with the python code, which can be used to construct queries and analyze their results, provide a very powerful tool for multiple validation purposes.

## 1.2 Terminology

***Table 1: UTDB API Terminology***

Some of the terminology mentioned below requires further explanations in latter sections of the document. Nevertheless, it is brought up here for reference.

| Term | Description | 
| ------ |---------- |
| Storage        |The persistent file (or files, or location) that contains data analyzable by UTDB capabilities. |
| UTDB API       |The Python API that is exposed to the user for uploading data to a storage and analyzing the data. |
| Data Uploading |The operation of taking some test execution output data and loading it to a storage. |
| Trace          |An API object that represents the persistent dataset to be analyzed: an ordered collection of records. |
| Metadata       |The information about the Trace schema: record-types and fields (names, types, etc.…). |
| Recode Type    |The type of the record in the Trace, for Traces that utilize multiple record-types. Each record-type may have a different set of fields. |
| Field | A field in the record that holds some data in the database. The field has a name, data type, and other attributes.|
| Query | An object that holds the user specific request for data from the UTDB. |
| Results | An object that holds the results of the user query. Its content depends on the query itself. |
| Flow detection | A pattern matching capability of UTDB that allows searching the data for collections of records that match a given pattern. |
| Event | A building block of flow-detection patterns. |
| Flow | A pattern that may be supplied to a flow detection query. Usually expresses a system behavior of interest. It is expressed in terms of events, their order and their data relations. |


## 1.3 UTDB Workflow
Using UTDB for trace post-processing analysis depends on test execution output files. The following are steps that are required for using UTDB for trace post-processing analysis. Click the link to get to get the detailed information for each step.

If the original data is not directly analyzable via UTDB API, it must be uploaded first. This step can be done once per test. After the data is loaded, multiple analysis operations can be done on the uploaded test data. There are two basic methods to load data:

1. ***Upload textual output files to UTDB storage*** using the provided data parsing Reader API.
2. ***Manually creating of UTDB storage*** using UTDB Writer API.

Once the data is available for UTDB API to work on, the typical data analysis flow involves the following steps:

1. ***Connect to a data storage:*** specify the data source to work on and obtain a Trace object.
2. ***Construct a query:*** specify the information to be retrieved from the trace for the desired analysis.
3. ***Execute the query:*** obtain the results of the constructed query. There are multiple execution methods for different purposes. For example, one execution method would just print out the resulting records, while another execution method would return a Python iterable to let users execute any custom Python code on the retrieved results.
4. ***Analyze the query results:*** perform any application-specific processing off the obtained records; for example checking the records against some expected data.
5. Return on steps 2-4 as necessary to achieve the application goal.

Another typical usage scenario is collecting functional coverage on the data in the trace.

1. ***Connect to a data storage:*** specify the data source to work on and obtain a Trace object.
2. ***Construct a coverage spec:*** specify covergroups, coverpoints and bins, along as the data values or queries that should be used to compute them.
3. ***Execute the coverage collection:*** obtain the functional coverage report in any of the supported formats; or a Python iterable to let users execute any custom Python code on the retrieved results.

The following sections contain detailed information on how to set up and use UTDB tool and UTDB API. 
_________________________________________________________________________________________________________________________________________________________________________________________________________
# 2. UTDB environment setup
## 2.1 UTDB version home directory
UTDB is installed under central location at:

***/p/hdk/rtl/cad/x86-64_linux26/dt/utdb***


The **UTDB_HOME** environment variable should be set to point to the specific UTDB version root directory.

In HDK environment **CAD_ROOT** is commonly used to point to the root directory of all PESG tools so it can be used to set up **UTDB_HOME** as follows:

***setenv UTDB_HOME <CAD_ROOT>/utdb/<UTDB_VER>***


In other environment (e.g. cheetah) **UTDB_HOME** can be set as follows:

***setenv UTDB_HOME /p/hdk/rtl/cad/x86-64_linux26/dt/utdb/<UTDB_VER>***


UTDB version naming convention is \<YY>.\<MM>.\<number>[p\<patch>] where:


+ \<YY> is two digits representing the year (e.g. 22 stands for 2022)
+ \<MM> is two digits representing the month (e.g. 02 stands for February)
+ \<number> is a running number representing a version within a month
+ \<patch> is an optional patch number

UTDB version examples:

*Version 23.02.4p1* is a patch 1 version for 23.02.4 major release

Setting **UTDB_HOME** environment variable:

***setenv UTDB_HOME /p/hdk/rtl/cad/x86-64_linux26/dt/utdb/24.08.2***

*UTDB.version* API can be used to access version components

***UTDB.version API usage:***

``` py
from UTDB import *

# for example, UTDB_HOME = /p/dt/cad/em64t_SLES12/utdb/24.08.2p1
print(version)            # 24.08.2p1
print(version.major)      # 24
print(version.minor)      # 8
print(version.micro)      # 2
print(version.patch)      # 1
print(version.string())   # 24.08.2p1
print(version.number())   # 24080201
print(version > 24080100)   # True
```

## 2.2 UTDB Python version
UTDB Python API is based in python version 3.6.3a.

Python version can be set in the script file as follows:

***Setting Python version for UTDB scripts:***
``` py
#!/p/hdk/cad/python3/3.6.3_gcc640/bin/python3

```

## 2.3 UTDB Python libraries search path
UTDB Python libraries are located under **UTDB_HOME/lib**.

Using **UTDB_HOME** in python script and setting the library search path can be done as follows:

***Adding UTDB PAIs library path:***
``` py
# import general purpose python lib API
import os, sys
 
# get UTDB_HOME from the environment
utdb_home = os.environ['UTDB_HOME']
 
# add UTDB path to python lib path
sys.path.insert(0,os.path.join(utdb_home,"lib"))

```

## 2.4 UTDB Python Modules
UTDB Python API comes in two packages.
The UTDB package that provides data access/query API capabilities:

***importing UTDB PAIs library path***
``` py
from UTDB import *

```
The data uploading capabilities are currently available in a separate uploader module:

***Importing uploader APIs***
``` py
from uploader import *

```
_________________________________________________________________________________________________________________________________________________________________________________________________________
# 3. Upload test data to UTDB storage
Uploading test data to UTDB storage is a mandatory first step for using UTDB for post-processing analysis. The uploading process can be done by using the uploader APIs for reading the test output file and writing its data to UTDB Storage, or by using TableWriter to directly write data to UTDB from Python code. UTDB storage is represented as a table of records where each record has a set of fields with names and types.

## 3.1 Uploading data from test log (tracker) file
Uploading a test output file to the UTDB storage, requires a set of parameters that include a list of fields names, type, and maybe other parameters. This parameter set is called Schema.

The Schema is provided to the Reader object. The Reader object reads the test output files and possibly returns a DataTable object that contains the read data in a table format.

At this stage it is possible to manipulate the data in the DataTable based on the output needs and finally send the DataTable to the Writer and store the data in UTDB storage.

If no data manipulation is required, it is possible to send the Reader object directly to the Writer and directly store the input data in UTDB storage.

The following section will describe how to set the uploader configuration, call the Reader, manipulate the data and write the data to UTDB storage.

See UTDB Creation section for more information


## 3.2 Uploader API library import
UTDB uploader module exists under **UTDB_HOME/lib**.

It should  be imported as follows:

***importing uploader APIs***

``` py

from uploader import *

```

## 3.3 Uploading configuration setup
Uploading test output to UTDB storage requires setting TableSchema configuration.

Uploading can be done either from textual output files, or directly to UTDB storage during test.

The TableSchema includes data fields configurations, so the reader and/or the writer will know what data to expect and how to handle it.

The data fields configuration is a list of Field objects that must contain the field name and fields data type.

In addition to that, other properties can be set:

- Input numeric string base (in case of number) default is DEC [*base* = Base.DEC]; may have a different value for each record-type (for traces that utilize multiple record-types)
- Null values text representation [**null_value**='--']
- Textual representation format string  [**format**='0x{:x}']; may have a different value for each record-type (for traces that utilize multiple record-types)
- Field placeholder – not read from input data [**mode**=RWMode.WRITE]
- Read only Fields – not written to the storage [**mode**=RWMode.READ]
- Integration to user defined python functions for data manipulation [**convert**=<method_name>]
- Improving performance using database index or lookup tables [**index**=True, **lookup**=True]

UTDB provides few common time converters (**ps_str_to_ps** , **ns_str_to_ps** , **us_str_to_ps**)  that converts the input string value into time field numeric value, and can also change the scale of the value from nanoseconds and microseconds to common picoseconds value.

Otherwise, the conversion method implementation is the user's responsibility. It must be able to accept a string parameter (the original field value for each line) and return final field value (with the type specified by the **type** configuration).

***Following is an example of a TableSchema configuration:***
``` py
# Create fields list
fields = [
    field(name='TIME', type=FieldType.INT, convert=ns_str_to_ps)
    field(name='TYPE', type=FieldType.STRING, lookup=True)
    field(name='DATA', type=FieldType.UINT, mode=RWMode.READ, base = Base.DEC),
    field(name='BIN_DATA', type=FieldType.UINT, base = Base.BIN),
    field(name='ADDR', type=FieldType.UINT, base = Base.HEX, format='0x{:x}'),
]
 
# Create TableSchema set fields via constructor
schema = table_schema()
 
# add anonymous record schema (without name)
schema.add_record_schema(fields)
 
# alternatively add record schema with record type name (mandatory for multiple record types)
schema.add_record_schema('my_record_type', fields)
 
# field definitions per record schema with different values of base and format
schema.add_record_schema('my_record_type1', [field(name='BIN_DATA', type=FieldType.UINT, base = Base.BIN), field(name='ADDR', type=FieldType.UINT, base = Base.HEX, format='0x{:x}')])
schema.add_record_schema('my_record_type2', [field(name='BIN_DATA', type=FieldType.UINT), field(name='ADDR', type=FieldType.UINT, base = Base.HEX, format='{:016X}')])

```

## 3.4 Reading test output textual file data
Test output file data reading is done using the uploader Reader object.

The Reader is initialized taking the input file and TableSchema. In addition, the following file parsing parameters can be set :

- *separator* (regex) – used to split each line to its fields
- *include* (regex) – used to filter in lines that matched the regex expression
- *exclude* (regex) – used to filter out lines that matched the regex expression

Once a reader is created, the **read()** method is used to read the input file data and return a DataTable object. Alternatively, the reader can be passed to the writer that will internally call the **read()** method.

The read method reads chunks of lines (10000 by default). This can be changed by using the *batch_size* parameter. For reading multiple batches the **read()** method can be used as iterator.

The Reader read method throws *UploaderReadError* exception in case of read errors. This can be used to review and handle input file or reader configuration issues.

***Following is an example of Reader usage:***
``` py
# Creating Table Schema
fields = […]
ts1 = table_schema()
ts1.add_record_schema(fields)
 
# Creating Reader object
reader = Reader(file_path='my_test_file.log', schema=ts1, separator='\|')
 
try:
    # Read data and get DataTable object
    for table in reader.read(batch_size=10, max_errors_per_batch=3):
    ...
except UploaderReadError as e:
    print(e)
    exit(input_file_path + " reading error occurred")

```

## 3.5 Using DataTable to manipulate the read data
The DataTable is a list of records with all the fields that where defined by the *TableSchema* configuration. Each field value can be set or accessed using python dictionary style access with the field name and the key.

*DataTable* can be generated by the Reader **read()** method or created manually using Python API.

The DataTable methods that are used for manual **DataTable** creation are **add_record_type()** which associates a record type name and its schema (as preparation for multi record type support) and **add_record()** which returns a record that can be used to set its data.

***Creating DataTable programmatically***
``` py
# Create DataTable with a schema
table = DataTable(schema)
 
# Add new record of 'common' record type
rec = table.add_record('common')
 
# set record fields data
rec['A'] = 1
rec['B'] = 2
rec['C'] = rec['A'] + rec['B']

```

***creating Table Schema from reader***

```py

# create Table Schema
fields = [field('A',...), field('B',...), field('C',...)]
schema = table_schema()
schema.add_record_schema('common', fields)
 
# Create Reader object
reader = Reader(file_path='my_test_file.log', schema=ts1, separator='\|')
 
# read log data into DataTable Reader read() method
for table in reader.read()
    for rec in table:
        rec['C'] = rec['A'] + rec['B']

```

## 3.6 Writing data to UTDB
Writing data from textual files to UTDB is done by using the uploader Writer **write()** method. The Writer instance is initialized with a UTDB connection string which usually contains the path to the target UTDB. There is an option to set a specific storage type (e.g. **pgpqt**).

The Writer **write()** method accepts DataTable object or the Reader object itself.

***Writing with the Reader***
``` py
# create data reader
reader = Reader(...)
 
# create writer with path to output UTDB
writer = Writer('my_utdb_location')
 
# use Writer direct write() from read() result
# this is the most efficient implementation as it all happens in C++
writer.write(reader)
 
writer.close()

```
***Writing using a Table***
``` py
# create data reader
reader = Reader(...)
 
# create writer with path to output UTDB
writer = Writer('my_utdb_location')
 
# use Writer write() with Reader created DataTable
for table in reader.read(...):
    # possibly iterate over each line in table and manipulate its data
    ...
    writer.write(table)
 
writer.close()

```
## 3.7 Writing data directly to UTDB
Writing data directly from Python tracker to UTDB storage is done using uploader Writer **write_row()** method. The Writer object is initialized with the type of the storage (e.g. **pgpqt**) and the path to the destination UTDB storage.

The table schema is provided to the Writer object via the **init()** method, and records are injected either as a list of values ordered according to the order of the schema fields, or a dictionary with the names of schema fields as keys.

***creating Table Schema from reader***
``` py
# create Table Schema
fields = [field('A',...), field('B',...), field('C',...)]
schema = table_schema()
schema.add_record_schema('rt', fields)
# initialize Writer object with schema
writer = Writer('my_utdb_location')
writer.init(schema)
 
# inject records to UTDB storage
writer.write_row([1,2,3], record_type='rt')
writer.write_row({'A': 4, 'B': 5, 'C': 6}, record_type='rt')
writer.write_row([7,8], record_type='rt') # Partial list of values. field 'C' remains empty (null value)
writer.write_row({'A': 9, 'C': 10}, record_type='rt') # Partial dictionary. field 'B' remains empty (null value)
 
writer.close()

```

## 3.8 Reading and writing data to UTDB
Uploading data from textual files to UTDB by using the **upload()** method.

The Writer and Reader instances are initialized as shown above,  and are being passed to the **upload()** method.

***Writing with the Reader***
``` py
# create data reader
reader = Reader(...)
 
# create writer with path to output UTDB
writer = Writer('my_utdb_location')
 
# read the data from textual trace and write to UTDB storage
upload(reader, writer)

```

## 3.9 Writing hierarchical data to UTDB
Uploading a **Datatable** with hierarchical structure using Writer **write()** method.

The Writer and Schema instances are initialized as shown above.

***Writing with the DataTable***
``` py
# create schema
schema = table_schema(hierarchical=True)
 
# create data table
table = DataTable(schema)
 
# create writer with path to output UTDB
writer = Writer('my_utdb_location')
 
# read the data from textual trace into the data table
# and write to UTDB storage
writer.write(table)

```

## 3.10 Writing data to UTDB and Text File
Writing data to both UTDB and text file is done by using the Writer object's open_text() method. This method is called before the init() method and takes the file path as an argument.

In the example below, the data is written to both the UTDB storage and the text file. 
```python
# create Table Schema
fields = [field('A',...), field('B',...), field('C',...)]
schema = table_schema()
schema.add_record_schema('rt', fields)

# initialize Writer object to write to both text file and UTDB
writer = Writer('my_utdb_location')
writer.open_text('my_text_file_location')
writer.init(schema)
 
# inject records to UTDB storage and text file
writer.write_row([1,2,3], record_type='rt')
writer.write_row({'A': 4, 'B': 5, 'C': 6}, record_type='rt')
writer.write_row([7,8], record_type='rt') # Partial list of values. field 'C' remains empty (null value)
writer.write_row({'A': 9, 'C': 10}, record_type='rt') # Partial dictionary. field 'B' remains empty (null value)
 
writer.close()
```

## 3.11 Discover Schema
Creating a schema from #header by using the **discover_schema()** method.

*schema_overrides** parameter is a dictionary of String and Field objects, allowing the user to change the default name, type, mode, etc.

***Using discover schema***
``` py
# create schema overrides dictionary
schema_overrides = {
    "Time" : field(name="TIME", type=FieldType.UINT),
}
  
# create schema using discover_schema
schema = discover_schema(file_path='my_file.log', schema_overrides=schema_overrides)

```

## 3.12 Uploading base classes
UTDB uploading base classes provides base classes for tracker files uploading, manual (any user data) uploading, and merging existing UTDBs.
Examples or the framework classes usages are located at **UTDB_HOME/examples/framework_examples**

uploading base classes includes 2 classes:

- **UploaderBase** class - for uploading data from tracker files or other sources into UTDB storage
- **MergerBase** class - for merging multiple UTDBs into one merged utdb

### 3.12.1 UploaderBase class
The uploading base classes provides the following functionality:

+ script arguments parsing (use --help for that info)
    + -i <input log/tracker file> (mandatory)
    + -O <destination directory> (optional. default is local dir)
    + -u <utdb name> (optional. default is input file name with "_utdb" at the end)
+ class members initialization:
    + **schema - empty** table schema
    + **input_file_path** - based on input parameter
    + **output_utdb_path** - based on input parameters or defaults
    + **writer** - initialized with output_utdb_path

User script that uses *UploaderBase* will include (among other uploading specific stuff ):
+ importing uploader module (`from uploader import *`)
+ creating uploader class and inherit from framework base class (`class TrackerUploader(UploaderBase):`)
+ override and implementing set_schema method (`def set_schema(self):`)
    + add one or more record schemas to the class table schema variable (self.schema.add_record_schema('idi', ...)) 
+ implementing **upload_data()** method (`def upload_data(self):`)
    + if using reader:
        + instantiate the reader (if using it to read tracker file) (`reader = Reader(file_path=self.input_file_path, schema=self.schema, ...)`)
        + call **upload()** with the created reader and writer objects (`upload(reader, self.writer)`)
	+ if manually getting the data:
		+ figure out the data to upload
		+ using writer write_row to upload created data to UTDB (`self.writer.write_row(...)`)
	+ create main function to have script entry point (`if __name__ == "__main__":`)
		+ create instantiate of uploader class and call **run()** method (`TrackerUploader().run()`)


***Using Uploading framework to read from file***
``` py
# ...
 
from uploader import *
 
# **************************************************************************************
# specific uploader class
# **************************************************************************************
class TrackerUploader(UploaderBase):
 
    # **************************************************************************************
    # user logic for setting uploader record schemas (called by framework)
    # **************************************************************************************
    def set_schema(self):
  
        # schema setting
        self.schema.add_record_schema('idi', [
            field(name="NUMBER", mode=RWMode.READ),
            field(name="REC_YPE", mode=RWMode.READ),
            field(name="TIME",  type=FieldType.UINT, format='{:15d}'),
            field(name="UNIT"),
            field(name="TID"),
            ...
        ])
  
    # **********************************************************************************
    # main uploading method (called by framework)
    # **********************************************************************************
    def upload_data(self):
 
        reader = Reader(file_path=self.input_file_path, schema=self.schema, include='^\d+', separator=',')
        upload(reader, self.writer)
 
 
# **************************************************************************************
# main function for command line usage
# **************************************************************************************
if __name__ == "__main__":
    TrackerUploader().run()

```

***Using Uploading framework to load user data***
``` py
# ...
 
from uploader import *
 

# **************************************************************************************
# specific uploader class
# **************************************************************************************
class ManualUploader(UploaderBase):
 
    # **************************************************************************************
    # user logic for setting uploader record schemas (called by framework)
    # **************************************************************************************
    def set_schema(self):
 
        # schema setting
        self.schema.add_record_schema('manual', [
            field(name='TIME', type=FieldType.UINT),
            field(name='INT_DATA', type=FieldType.UINT),
            field(name='STRING_DATA'),
        ])
 
    # **********************************************************************************
    # main uploading method  (called by framework)
    # **********************************************************************************
    def upload_data(self):
 
        # upload data
        self.writer.write_row({"TIME":1, "INT_DATA": 100}, record_type='manual')
        self.writer.write_row({"TIME":3, "STRING_DATA":"3 hundred"}, record_type='manual')
        self.writer.write_row([2,200, "2 hundred"], record_type='manual')
 
# **************************************************************************************
# main function for command line usage
# **************************************************************************************
if __name__ == "__main__":
    ManualUploader().run()

```

### 3.12.2 MergerBase class
The merging base classes provides the following functionality:
+ script arguments parsing (use --help for that info)
	+ -I <source UTDBs directory> (optional. default is local dir)
    + -i <list of source UTDBs names or patterns>
	+ -O <destination directory> (optional. default is source UTDBs directory)
	+ -u <utdb name> (optional. default is "merged_utdb")
+ *MergerBase* class members initialization:
	+ **schema** - empty table schema
	+ **input_utdbs_dir** - based on input parameter
    + **input_patterns** - list of utdb name or patterns to merge
	+ **output_utdb_path** - based on input parameters or defaults
	+ **sources** - dictionary of utdb name to *MergerSource* class instance that represents the UTDB source attributes and functionality. with their name, trace object and query object
+ *MergerSource* class:
	+ Class members:
		+ **name** - the name of the UTDB source
		+ **trace** - the UTDB trace instance that can be used for example to create output fields that are based on existing fields value(s)
		+ **fields_list** -  list of trace fields.
		+ **record_types_overrides** - dictionary that enables changing record type names (see view documentation for more details)
	+ Class methods:
		+ **remove_field(field_name)** - remove field by name from the fields list
		+ **insert_field(new_field, field_index = None)** - new field in some *output_field* created by the user
		+ **replace_field(field_name, new_field)** - replaces existing field by name with new field 
		+ **field_index(field_name)** - get field index by name
		+ **rename_record_types(overrides_dict)** - set new value for record_types_overrides
		+ **get_view()** - get view object that that is created from query the trace with the user modifications (used in **union_view()** method call)
+ Creating output fields
	+ creating output fields and other utdb field operations requires UTDB module API  
	+ for that matter importing uploader from uploader import *, also import UTDB as utdb (to eliminate possible module functionality conflicts)
	+ so in order o use UTDB API the utdb.  prefix is required


User script that uses *MergerBase* will include (among other uploading specific stuff ):

+ importing the framework,  `from uploader import *`
+ create merging class and inherit from framework base class `class ExplicitMerger(MergerBase):`
+ implement and override **add_sources()** method `def add_sources(self):`
	+ use base class method to add sources paths to merge and potentially give it explicit name `self.add_source(...)`
	+ **add_source()** method signature is `def add_source(self, utdb_path, src_name=None)`
	+ the default source name is the utdb name
+ optionally implementing and **adjust_sources()** method `def adjust_sources(self):`
	+ this enables doing manipulation to added sources for better alignment in the merge utdb
	+ use base class **get_source()** method (by name) to get a source object to modify `src = self.get_source('cpurequest_utdb')`
	+ remove existing fields  `src.remove_field('ADDRESS')`
	+ insert new field using user defined output field construct `src.insert_field(utdb.output_field(...))`
	+ replace existing field with user defined output field `src.replace_field("OPCODE", utdb.output_field(...))`
	+ change record type name using dictionary from original record type to new record type name `src.rename_record_types({src.trace.cpurequest : 'newrequest'})`


***Using Uploading framework to merge UTDBs***

``` py
# ...
 
from uploader import *
 
# **************************************************************************************
# specific merger class
# **************************************************************************************
class ExplicitMerger(MergerBase):
 
    # **********************************************************************************
    # add sources for merging
    # **********************************************************************************
    def add_sources(self):
 
        self.add_source(os.path.join(utdb_home,"examples","traces","cpurequest_utdb"))
        self.add_source(os.path.join(utdb_home,"examples","traces","nbresponse_utdb"))
 
    # **********************************************************************************
    # adjust sources query fields
    # **********************************************************************************
    def adjust_sources(self):
         
        src = self.get_source('cpurequest_utdb')
        if src:
            # remove existing field
            src.remove_field('ADDRESS')
 
            # insert new field
            src.insert_field(utdb.output_field("DATA_PLUSE_1", src.trace.all.DATA+1,format='{:x}'))
 
            # replace existing field
            src.replace_field("OPCODE", utdb.output_field("OPCODE", src.trace.all.OPCODE + "_rpl"))
 
            # change record type name
            src.rename_record_types({src.trace.cpurequest : 'newrequest'})
 
 
# **************************************************************************************
# main function for command line usage
# **************************************************************************************
if __name__ == "__main__":
    ExplicitMerger().run()

```

-----
# 4. Connecting to data storage and working with metadata

## 4.1 Connecting to UTDB data storage
Prior to any work with data, there is a need to connect to the relevant data source using the **connect()** function. The **connect()** function accepts a *connection string* argument and returns a Trace object that represents the data. The Trace object enables exploring the schema of the data (the metadata: information about fields and record-types present in the trace), construction of queries, etc.

The connection string represents the location of the source data and optional parameters required to start working with that data. In the most general case, the connection string has a URI syntax. Please consult the Reference Guide for the full syntax. For most cases, assuming UTDB data exists on a file system, the connection string will just be the full directory path of the UTDB database. For example:

``` py
# connect function usage example
trace1 = connect('/nfs/site/…/my_utdb')
 
# connect function usage example including specific utdb storage type ('pgpqt') as URI prefix
trace2 = connect('pgpqt:/nfs/site/…/core_tree_view_utdb')

```

## 4.2 Connecting to Jem trace
The connection to a Jem trace is done similarly, by providing a path to the Jem trace index file.
 ``` py
# Connect to a Jem trace. Specify "pgjem" as the type of the storage.
trace1 = connect('pgjem:/nfs/mytrace/tlm_trace_index.txt')
```

In some cases, it will be necessary to use *dbso* parameter to provide path(s) to Jem-generated code (shared libraries typically named libtlmgen<___>.so), typically located in the model build output area. Modern Jem versions will try to automatically identify that location based on the information present in the trace, but it may not always be possible (e.g. if the files were moved to a different location). Multiple paths may be provided, separated by plus-sign '+'.

``` py
# Connect to a Jem trace. Explicitly point to Jem-generated code location (with _db in the name).
trace1 = connect("pgjem:/nfs/mytrace/tlm_trace_index.txt?dbso=/nfs/myarea/output/jem/models/mymodel/libtlmgen_db.so")
```

An optional parameter *src* may be supplied to explicitly limit the amount of data read from the trace to that originating from specific monitors. This may potentially improve runtime of queries. (Such selection can also be expressed as part of queries, but might be slower.) If the optional *src* parameter is present, only the data of specified will be loaded. Multiple sources of interest may be specified, separated by plus-sign '+'. A perl-style regular expression enclosed in parentheses may be used. Use double-quotes to avoid parsing ambiguities when using various special characters.

``` py
# Connect to a Jem trace. Explicitly point to Jem-generated code location, and specify two regex patterns to select originating monitors.
trace1 = connect('/nfs/mytrace/tlm_trace_index.txt?dbso=/nfs/…/jem/models/mymodel/libtlmgen_db.so;src="(.*my_ip_1.*)"+"(my_ip_2.mymon.myport$)"')

```

In the current version, connecting to Jem trace requires the trace to be recorded in one of the following formats:

* x64_indexed_var_size_multi_source_format (recommended for simulation)
* x64_fixed_size_multi_source_format
* x64_fixed_size_single_source_format (required for emulation)

Configuration of the trace format during recording is controlled by Jem's environment variable **JEM_TLM_TRACE_FORMAT**. It should be set to one of the above values. See Jem documentation for more details. 

## 4.3 Using Trace object and metadata
The trace object, obtained from the connect call, exposes the *trace.all* collection of all fields in the trace. The access to individual fields may be done as to members of that collection. The fields themselves are objects that expose name and type attributes. A sequence of all fields is also available.

``` py
# access a specific field reference
f = trace.all.FIELD1
 
# access the name of a field reference
f.name == 'FIELD1'
 
# access the datatype of a field reference
f.type == DataType.UINT
 
# The Python object that behaves as ordered list of fields in the record-type, 
# enabling manipulation of these fields by their names, including operations like **replace**, **rename**, **remove**
for f in trace.all.fields:
    print(f.name, " : ", f.type)

fl = trace.all.fields
if 'DATA' in fl:
    fl.remove('DATA')
fl.replace('ADDRESS', output_field('ADDR_HIGH', trace.all.ADDRESS[16:8]))
fl.rename('COREREQID', 'CID')
fl.insert(3, output_field('SOURCE', 'my_source'))

```

When trace data utilizes multiple record-types, the trace object also exposes the information about the record-types and which fields they contain. To refer to fields of a specific record-type, the name of the record-type is used instead of the **all** fields collection. Note that the same field of the trace may be accessed either via the *all* collection or via the specific record-type it is part of. There is a subtle difference in such accesses in certain contexts, namely in expressions that act as condition (e.g. for filtering the data).

``` py
# Referencing fields of req record-type
trace.req.OPCODE
trace.req.ADDRESS
 
# The Python object that behaves as ordered list of fields in the req record-type 
trace.req.fields
 
# Referencing fields of any record type via trace.all collection.
trace.all.TIME
trace.all.OPCODE
 
# A collection of all record-types present
trace.record_types

```

For a trace created via uploading mechanisms described earlier, the schema - the collection of record-types and fields, their names and data types - was determined at the time of uploading. Exactly the same records-types and fields will be available via the trace object after calling **connect()**, as were specified in the schema for the Writer API.

For a Jem trace, the schema always looks identical. There are no record-types in such trace, and fields are only accessed via **trace.all** collection. The Jem trace contains a record per event/transaction recorded during test execution. The records have four fields:

* **trace.all.TIME** : a uint64 field indicating the timestamp of the record;
* **trace.all.PAYLOAD_TYPE** : a string field indicating the SystemVerilog type name of the recorded event (typically a SystemVerilog struct);
* **trace.all.SOURCE** : a string field indicating the origin of the record (e.g. the full RTL path of hw-monitor port that sent the payload);
* **trace.all.DATA** : the actual payload of the record.

The *trace.all.DATA* field is somewhat special, compared to all other UTDB fields. Since different data-sources in the Jem trace, e.g. hw-monitors, send out payloads of different data types, this field does not have a single pre-defined datatype, but may contain values of different types. In database parlance this is called a VARIANT field. In standard programming languages, including SystemVerilog, this can be thought of as a *tagged union*: a datatype used to hold a value that could take on several different, but fixed, types. Only one of the types is in use in each specific record. More details on working with *trace.all.DATA* field are described below.

----
# 5. UTDB expressions
Two kinds of expressions are distinguished in the UTDB API:

* Value expressions: expressions that compute values; these expressions are described in this section.
* Flow expressions: expressions used to construct patterns for the flow-detection capability; these expressions, described in a separate section, don't compute values, but instead express temporal relations between records.

Value expressions are used in a variety of contexts, such as filtering conditions, sorting keys, specification of computed fields, etc. The datatype of the value produced by an expression depends on its operands and the expression semantics. Expressions and fields  can have a special null value (represented as None in Python), which indicates the absence of a value. Note that for some data types, which also have a notion of “empty value”, such as strings, the null value is not the same as the empty value. Null value used in boolean context is treated as false.

Generally speaking, a value expression is one of the following:

1. A native Python expression evaluated by Python interpreter;
2. A field expression
3. Application of a built-in operator or function on a sub-expression(s)

## 5.1 Field Expressions
Trace fields can be used in expressions by referring to them using the trace object. For example: 

``` py
# Field expressions
trace.req.OPCODE
trace.resp.ADDRESS
trace.all.TIME

```

Referring to a field via *trace.all* container or via a record-type, such as trace.resp in the example above, is semantically equivalent in most cases, except in certain contexts explicitly mentioned in this document. In certain contexts, such as in conditions appearing in **where()** or **event()**, referring to a field via a record-type implies checking that the record is indeed of the mentioned type.

## 5.2 Slice operators
Slicing operator **[]** is used to extract specific bits from integer expressions or substrings from strings. Slicing can be done using a single index to select a single bit/char, or using a range of indexes to select a bit-range/substring.

For integer expressions the index/indices in the slice are mandatory, non-negative integers.

For string expressions the indices are optional, where a missing start index means "from beginning" and a missing end index means "to end". Negative index values are interpreted as reverse indices, counting from the end of the string.

``` py
# Slice expression -- numeric value single bit 4 slicing (0 based index)
trace.req.ADDR[3]
 
# Slice expression -- numeric value single multi bits 4 to 8 (inclusive)
trace.req.ADDR[8:4]
 
# Slice expression -- string value single character third character slicing         # (0 based index)
trace.req.OPCODE[2]
 
# Slice expression –- string value of third character to the end
trace.req.OPCODE[2:]
 
trace.req.OPCODE[1:4] #substring from position 1 to 4 (not included)
trace.req.OPCODE[:3]  #substring from start to position 3 (not included)

```
## 5.3 Built-in operators
Standard python operators are supported with their native precedence. Arithmetic and relational operators carry the standard Python semantics. Bitwise operators ("**&**", "**|**", "**~**") are overloaded to represent logical and/or/not respectively. Care should be used to use parentheses around operands of theses operations, as they have high precedence in Python. Bitwise operations are instead performed by built-in functions **bit_and()**/**bit_or()**/**bit_xor()**/**bit_not()**/**bit_lshift()**/**bit_rshift()**. 

Arithmetic, relational and bitwise operations on null values produce a null result.

``` py
# Arithmetic expression examples
trace.resp.ADDR + 123           # 'plus' for numeric values
trace.req.DEST + 'ABC'          # concatenation for string values
 
# comparison expressions
trace.req.DEST == 'CPU'
1000 < trace.all.TIME
trace.req.ADDRESS == (Trace.req.DATA + 0xA0)
 
# comparison expressions with multiple values
trace.all.TIME.in_list([1000, range(2000,3000), 5000])  # numeric value from list
in_list(trace.req.DEST+'ABC', ['XABS', 'YABC', 'ZABC'])     # string value from list
 
# logical expressions
(trace.req.DEST != 'CPU') & (100 < trace.all.TIME)
~(trace.resp.DATA == 0xFFF) | (trace.req.ADDRESS / 2 < 0xA1)

```
## 5.4 Functions for bit pattern analysis
Bitwise operations are supported on unsigned integers. See reference manual for the full list of supported operations.

``` py
# return the smallest integral power of two not less than the given field
bit_ceil(to_uint(trace.req.ADDR))
 
# return the number of consecutive 0 bits, starting from the most significant bit
countl_zero(to_uint(trace.req.ADDR))
 
# return the number of 1 bits in the field
popcount(trace.req.TIME)
 
# return the result of bitwise left-rotation
rotl(to_uint(trace.req.ADDR), 4)
 
# return the result of bitwise right-rotation
rotr(to_uint(trace.req.ADDR), 7)

```

## 5.5 Functions for null checking
Expressions can have a special null value, which indicates an absence of value. Functions **exists**/**is_not_null** and **not_exists**/**is_null** can be used to check null value of expression of all data types. These functions can be used as methods of fields, or as global functions.

Note that for data types that have both null value and empty value (e.g. string), the null value is not the same as the empty value.

``` py
# check if fields value in NULL or not
trace.req.DATA.exists()
trace.resp.ADDR.not_exists()

```

## 5.6 Functions for string matching 
There are specific functions that can be used for matching expressions of type string. String matching operations can be used as methods of string fields or as global functions on any string expression.  The following example demonstrates two options to call **contains()** method. Two calls produce the same results.

``` py
# calling Field Expression method 'contains'
trace.req.OPCODE.contains('ME')
 
# calling global function 'contains'
contains(trace.req.OPCODE, 'ME')

```

All string matching functions have **ignore_case** boolean parameter that can be set to True for case insensitive mode.

``` py
# True if OPCODE begins with 're' 'Re' 'rE' 'RE'
trace.req.OPCODE.begins_with('Re', ignore_case=True)

```
The **match()** method has an additional **kind** parameter that can be set to ‘regex’ (default) or ‘wildcard’ to specify search mode. ‘wildcard’ mode allows using ‘*’ in pattern which means any sequence of zero or more characters. Following are a few examples of string matching operations:

``` py 
# True if starts with ‘R’/’r’ and ends with 'D'/'d'
match(trace.req.OPCODE, 'R*d', ignore_case=True, kind='wildcard')
 
# True if OPCODE ends with 'Read'
trace.req.OPCODE.match('^.*Read$', kind='regex')

```

## 5.7 Miscellaneous functions
**record_type()** function is provided to check the record-type of the record (see UTDB Trace Metadata description). The function evaluates to True if the record is of the given record-type.

``` py
# True if record type is ‘req’
record_type(trace.req)
 
# True if record type is ‘req’ or ‘resp’
record_type(trace.req) | record_type(trace.resp)

```
The conditional **if_** function provides the if-then-else behavior. The function receives 3 arguments. The first argument evaluates as boolean expression, while the 2nd and 3rd as values. The return value of the function is the 2nd argument if the 1st argument evaluates to True, otherwise the return value is the 3rd argument.

``` py
# True if OPCODE is 'Read' and ADDR is 0xA1, or if OPCODE is not 'Read' and ADDR is 0xA0
if_(trace.req.OPCODE == 'Read', trace.req.ADDR, trace.req.ADDR + 1) == 0xA1

```
**switch()** function provides a switch-case behavior. The function receives 2 mandatory arguments. The first argument is the switch-case expression, and the second argument is an expression→expression dictionary. An optional 'default' keyword argument can be added. The function returns the first value from the dictionary, with a corresponding key that evaluates as equal to the switch-case expression. If no keys evaluate as equal to the expression, the default value is returned.

``` py
# if DATA is equal to 0 returns "SUCCESS", otherwise if DATA is equal to 1 returns "FAILURE", otherwise returns "UNKNOWN"
switch(trace.all.DATA, {0 : "SUCCESS", 1 : "FAILURE"}, default="UNKNOWN"

```
**first_non_null()** function returns the first non-null expression from a list of expressions. If all expressions evaluate as null, the function returns null.

``` py
# returns the value of ADDRESS if it is not null, otherwise the value of DATA if it is not null, or finally returns null value.
first_non_null(trace.all.ADDRESS, trace.all.DATA) == 0xA1

```
## 5.8 Casting functions
Casting function can be used to convert expressions to a different datatype, as well as to convert between numeric and string representations of numbers. The full list of conversion functions is available in the reference guide. The most frequently used ones are shown below, in the context of declaring computed fields:

``` py
# convert OPCODE number to decimal number string
output_field('OPC_STR', to_str(trace.all.OPCODE))
 
# convert hexadecimal string to int number
output_field('int_num', to_int('-0XAbC'))
 
# convert number to binary string including '0b' prefix
output_field('bin_str', to_bin(1, base_prefix=True))
 
# convert number to binary string including '0x' prefix using upper case letters
output_field('hex_str', to_hex(trace.all.ADDRESS, base_prefix=True, upper_case=True))

```

---
# 6 UTDB query construction
UTDB query defines the data set that can be used in further operations. UTDB API distinguishes between query construction and execution, hence the construction doesn’t retrieve any data. The query construction is performed by chaining construction functions:

| Function | Method |
| ------ | ----------- |
| Select the source of the data | **from_()** |
| Select collected fields | **fields()** |
| Filter trace records | **where()* |
| Sort the results records | **sort_by()** |
| Limit the number of results | **limit()** |
| Get the first or last number of items | **first()** / **last()** |
| Group the results by field value | **group_by()** |
| Apply condition on group results | **having()** |


The construction functions use UTDB expressions. Each function is optional, but at least one must be present to construct a query. The order in which different query constructing functions are applied is not important. However, certain orders are often more natural to use for readability.

``` py

# Specify origin
query1 = from_(trace)
 
# Select fields to be obtained
query2 = query1.fields(trace.all.DATA, trace.all.TIME)
 
# Filter out irrelevant records
query3 = query2.where(trace.all.TIME > 1000)
 
# Sort the records
query4 = query3.sort_by((trace.all.TIME, DESC))
 
# Limit the set
query5 = query4.limit(10)
 
# get last results of the set set
Query6 = query4.last(3)

```
## 6.1 Select the source of the data
Query element that needs to be defined is the explicit source of the required data. The source can be a complete Trace, Query or other objects that will be reviewed later in the document. The method used to specify the query source is **from_()**. If from_ is not specified, the tool will automatically extract the trace that is used to build the other elements of the query.

``` py

# selecting the entire trace as the source of the query
query = from_(trace)
 
# defining query1
query1 = fields(trace.reqs.TIME, trace.reqs.OPCODE, trace.reqs.DATA)
 
# selecting query1 to be the source of query2
query2 = from_(query1)

```

## 6.2 Select collected fields
When constricting a query, specific fields can be defined to appear in the result. This can save time and memory usage during query execution. Selecting specific fields to collect is done by calling the **fields()** method. If fields are not specified, all the records fields will be obtained.

``` py
# creating new query using fields method
query1 = fields(trace.reqs.TIME, Trace.reqs.OPCODE)
 
# results example:
# (TIME=1234, OPCODE='WRITE')
 
# adding additional field to existing query using fields method on existing query
query2 = query1.fields(trace.reqs.DATA)
 
# results example:
# (TIME=1234, OPCODE='WRITE', DATA=0x2345)

```

### 6.2.1 Define user output fields
Output fields are utdb fields elements defined by the user. An Output Field is created by calling the **output_field()** object constructor define a name and some utdb value expression that results in some value. Output field can be used to get some value from multiple fields or to do some manipulation on a field. Also, it can be used for aggregation functions like **count()** or **sum_()**. An optional keyword argument *format* can be added with python formatting string. Format string is used to format string representation of the fields values in dump API and GUI.

``` py
# get sum of data and address
out_field = output_field("DATA+ADDR", trace.reqs.DATA + trace.reqs.ADDRESS, format="{:#X}")
 
# get reqid + 2
out_field = output_field("computed", trace.all.COREREQID + 2)
 
# get count of all the results
out_field = output_field("acount", count())

```

## 6.3 Filter trace records
In most cases the trace analysis does not require all the records from the database. For that matter there is a need to filter out the records with the data for the analysis. Filtering the records is done by calling the **where()** method. **where()** method accepts a UTDB boolean used by the query to filter the collected records.

``` py
# creating new query using where method
query1 = where(trace.res.ADDR != 0x1234)
 
# adding additional filter to query1 using where method on the query object
Query2 = query1.where(trace.res.TIME > 100)

```

## 6.4 Sort the results records
In some cases, sorting the records simplifies their analysis or even viewing. The **sort_by()** method enables defining the order between the records in the result. The order can be defined using value expressions and not only fields. Ascending and descending order is supported. **sort_by()** method can be nested so you can have a primary sort parameter and a secondary parameter (sorted inside the same primary parameter value).

``` py
# sort by calculated value in the ascending order
query1 = sort_by((trace.res.ADDR % 0xFFFF, ASC))
 
# and then, sort by TIME in the descending order
query2 = query1.sort_by((trace.res.TIME, DESC))

```
## 6.5 Limit the number of results
Not always the whole result set is required and it’s enough to look only on a subset of it. **limit()** method enables defining a limit for the number of the retrieved records and optionally to define an offset to start count the records.

``` py
# limit the amount to 10
query1 = where(trace.all.TIME > 1000).limit(10)
 
# limit the amount (10), but start from record 5
query2 = where(trace.all.TIME > 1000).limit(10, 5)

```
## 6.6 Get the first or last number of items
In cases where we need only the first or last item (or items) in the results the **first()** and **last()** methods can be used.

``` py
# get the first 10 items after time is 1000
query1 = where(trace.all.TIME > 1000).first(10)
 
# get the last 5 items before time is 1000
query2 = where(trace.all.TIME < 1000).last(5)

```

## 6.7 Group the results by field value
Grouping results is very useful in cases where some statistics on the data is required (e.g. counting or accumulation of values in some group) and in order to organize the results in some specific structure.

Grouping the results is done by calling the **group_by()** method and providing the one or more fields that needs to be used for the grouping (multiple levels).

The results of **group_by()** method is one record for each distinguished value of the group by field that was found in the query records (or cross product of multiple fields values).

``` py
# group by single field
query1 = group_by(trace.all.ADDRESS)
# results example:
# (ADDRESS=100)
# (ADDRESS=200)
# (ADDRESS=300)
# ...
 
# multi-level group by using 2 fields
query2 = group_by(trace.all.ADDRESS , trace.all.COREREQID)
# results example:
# (ADDRESS=100, COREREQID=5)
# (ADDRESS=100, COREREQID=10)
# (ADDRESS=200, COREREQID=5)
# (ADDRESS=200, COREREQID=30)
# (ADDRESS=300, COREREQID=40)
# ...
 
# multi-level group by using multiple calls
Query3 = group_by(trace.all.ADDRESS).group_by(trace.all.COREREQID)
 
# group by output field
Query4 = group_by(output_field("computed", trace.all.COREREQID + 2))
# results example:
# (computed=100)
# (computed=200)
# (computed=300)
# ...

```
## 6.8 Apply condition on group results (Having)
When using **group_by()** (see above) it is sometimes required to apply some condition on the groups of interest. Applying a condition to group results is done by calling the **having()** method.

The basic difference between the *where* and *having* conditions is that *where* is applied on the original table records before the grouping is applied, while *having* is applied on the grouping results after the grouping is done (see more info and examples in SQL documentation). If **group_by()** method is not used, the **having()** method acts like a simple **where()** method. 

``` py
# apply condition on group by COREREQID having COREREQID > 10
query1 = group_by(trace.all.COREREQID).having(trace.all.COREREQID > 10)
# results example:
# (COREREQID = 30)
# (COREREQID = 40)
# ...
 
# apply condition output field with group by
output_field = output_field("computed", trace.all.COREREQID % 4)
query2 = from_(trace).group_by(output_field).having(output_field == 1)

```
## 6.9 Parameterized query
A parameterized query is used to create several, sometimes many, queries with identical syntactic structure but differing from one another by certain values. To accomplish that, value placeholders can be used in query construction. A value placeholder is an object constructed by **bindparam()** function (or **P()** alias for the shorter code) with a unique key that identifies it. Then, the parameter can be used anywhere in value expression. Multiple placeholders can be used, or the same placeholder can be used multiple times within the same query construction. 

A parameterized query can be concretized explicitly using **bind()** function to produce a list of concrete queries given a mapping of placeholder keys to the actual values they should be substituted with. Multiple uses of **bindparam()** function with the same argument key return placeholders that will get substituted with the same value during binding.

``` py
# Consider the following motivating example. Given the following trace:
#   OPCODE  REQTYPE DATALEN
# 1 READ    C2U     16
# 2 READ    U2C     8
# 3 WRITE   C2U     32
# need to create a family of queries for each pair of OPCODE and DATALEN, each query returning the C2U
# requests for a specific pair
 
# Assume OPCODE can be one of {READ, WRITE}; and DATALEN can be one of {8, 16, 32}
opcodes = [“READ”, “WRITE”]
datalens = [8, 16, 32]
  
# create Bindparam object for opcodes (using alias P)
opcode_param = P('opcode')
  
# create Bindparam object for datalen
dl_param = bindparam('dl')
 
trace = connect(...)
 
# event without parameter
c2u_req_e = (trace.all.REQTYPE == "C2U")
# event with 'opcode' parameter
opcode_e = (trace.all.OPCODE == opcode_param)
# query with parameterized expressions
c2u_opcode_x_dl = where(c2u_req_e & opcode_e & (trace.all.DATALEN == dl_param))
  
# generate list of queries for all possible pairs <opcode,datalen>:
# <"READ",8>, <"READ",16>,...<"WRITE,32>
q_list = bind(c2u_opcode_x_dl, {opcode_param: opcodes, dl_param: datalens} )
 
# q_list will contain the following 6 queries
# where((trace.all.REQTYPE == "C2U") & (trace.all.OPCODE == "READ") & (trace.all.DATALEN == 8)
# where((trace.all.REQTYPE == "C2U") & (trace.all.OPCODE == "READ") & (trace.all.DATALEN == 16)
# where((trace.all.REQTYPE == "C2U") & (trace.all.OPCODE == "READ") & (trace.all.DATALEN == 32)
# where((trace.all.REQTYPE == "C2U") & (trace.all.OPCODE == "WRITE") & (trace.all.DATALEN == 8)
# where((trace.all.REQTYPE == "C2U") & (trace.all.OPCODE == "WRITE") & (trace.all.DATALEN == 16)
# where((trace.all.REQTYPE == "C2U") & (trace.all.OPCODE == "WRITE") & (trace.all.DATALEN == 32)

```
## 6.10 Hierarchical data queries
Hierarchical trace is a trace in which records have parent-child relationships, altogether forming an ordered collection of trees. Each record may have at most one direct parent (also called direct ancestor), and zero or more direct children (also called direct descendants). This rule dictates the tree structure. A record without a parent is called a *Root* record and a record without children is called a *Leaf* record.

UTDB APIs provide a set of hierarchical methods that can operate on a hierarchical trace in the query **where()** method (filter) boolean expression. The hierarchical expressions can refer to *Leaf* records, *Root* records, parents and children of records.

Hierarchical methods operate on some record-selector that is by itself defined as a **where()** method. In addition, hierarchical can be inclusive, meaning including the record-selector itself in the results.

The supported hierarchical methods are:

| Method | operation |
|--------|-----------|
| **is_root()** | True if record is a root (no parent) |
| **is_leaf()** | True if record is a leaf (no children) |
| **child_of_root()** | True if record is a child of a record in the <record-selector> result and a root |
| **child_of()** | True if record is a child of a record in the <record-selector>result |
| **parent_of()** | True if record is a parent of a record in the <record-selector> result |
| **parent_or_child_of()** | True if parent_of or child_of are True |

``` py

# return root records with TIME less then 3
q0 = from_(trace).where(is_root() & (trace.all.TIME < 3))
 
# return leaf records with OPCODE 'Read'
q1 = from_(trace).where(is_leaf() & (trace.all.OPCODE == 'Read'))
 
# return children of record with OPCODE 'Read'
q2 = from_(trace).where(child_of(where(trace.all.OPCODE == 'Read')))
  
# return children of root where root STATUS is 'COMPLETE'
q3 = from_(trace).where(child_of_root(where(trace.all.STATUS == 'COMPLETE') )))
 
# return parents of records with OPCODE 'Read', and TIME > 0 or TIME field is None
q4 = from_(trace).where((trace.all.TIME>0) | trace.all.TIME.is_null()).where(parent_of(where(trace.all.OPCODE == 'Read'), inclusive=True)
 
# return parents or children of records with OPCODE 'Read'
q5 = from_(trace).where(parent_or_child_of(where( (trace.all.OPCODE == 'Read') )))
 
# return parents of records with COREREQID >10 and children where DATA is None
q6 = from_(trace).where(parent_of(where(trace.all.COREREQID >10)) & child_of(where(trace.all.DATA.is_null()), inclusive=False))

```

A given hierarchical source (Trace/View/Result of nested Query) can be accessed as hierarchical, i.e. considering the parent-child relationships, or as flat, i.e. ignoring the parent-child relationships between the records and ***ignore_hierarchy*** boolean flag of **from_()** or **union_view()** methods allow to control it.  By default, the result will be hierarchical if the source is hierarchical. 

Limitation: currently sort_by and group_by queries may be invoked on flat data only

## 6.11 Retrieve and handle UTDB Data
Once a query or a view are created, there are 3 methods to get their data, where each method handles the results in a different way:
* The **fetch()** method retrieves the data and returns an iterable python object for further python analysis of the data.
* The **fetch_count()** method returns the number of records retrieved from the trace without the actual result.
* The **dump()** method creates textual columnar format of the results and prints them to the screen or into a file (currently supporting psv and csv format).
* The **store()** method retrieves the data and stores it in UTDB (non human readable format to enable further querying or analysis by external tools).

``` py

# fetch all data using from_ query constructor
results = fetch(from_(Trace))
 
# fetch a query using fields query
query1 = fields(trace.reqs.TIME, Trace.reqs.OPCODE)
results1 = fetch(query1)
 
# fetch a query using where filter on the prev fields selection
query2 = query1.where(trace.res.TIME > 100)
results2 = fetch(query2)
 
# fetch_count to get the number of records that the query find in the trace
num_results = fetch_count(query2)
 
# dump result data to "my_results.txt" file in psv (pipe separated) format
dump(query2, output="my_results.txt", output_format="psv")
# results example
# TIME        | OPCODE
# --------------------
# 200         | Read
# 300         | Write
 
# store results data to "my_query_utdb" database
store(query2, "my_query_utdb")

```

## 6.12 Access data via results iterator
Once results were fetched from UTDB and results iterator was returned it can be used to access the data. Results object is built out of data records that represent data returned from the database.

The top level results records are retrieved using Python iterator. The next level records (if exists, and depends on the query) are accessed using the **UTDB_CHILDREN** attribute iterator.

``` py

# fetch all data using from_ query constructor
results = fetch(from_(Trace))
 
# iterate and print top level results records
for rec in results:
    print(rec)
 
# iterate and print next level of results records
for rec1 in results:
    for rec2 in rec1.UTDB_CHILDREN:
        print(rec2)

```

### 6.12.1 Result records structure
The data records retrieved from the results iterator represent the data as retrieved from the database and constructed by UTDB depending on the query. The records behave as Python named tuples. Each field in the results can be accessed both by index or by name using attribute access (dot notation). The data record is immutable, and consists of native python types: boolean, int, float, str.
``` py
# fetch all data using from_ query constructor
results = fetch(from_(Trace))
 
# iterate and print top level results records
# align numeric TIME value in print, and use FLAG boolean value to print single char
for r in results:
    print(f"time: {r.TIME:>16}, opcode: {r.OPCODE}, flag: {'T' if r.FLAG else 'F'}")
```

**Additionaly values can consist of Jem data object resembling SystemVerilog types.**

These objects can consist of various data types, including structs, unions, arrays, and enums. For example, consider the SystemVerilog payload type declared as follows:

``` py
typedef enum logic [3:0] {
    IP_CMD_UNDEFINED,
    IP_CMD_READ,
    IP_CMD_WRITE,
    IP_CMD_CLEAR
} t_ip_cmd;

typedef struct packed {
    t_ip_cmd cmd;
    logic [3:0] addr;
} t_ip_mon_cmd_payload_s;

typedef struct {
    t_ip_mon_cmd_payload_s cmd;
    logic [31:0] data [1:0];
} t_ip_mon_data_payload_s;
```
And given a results iterator for the following query
``` py
# Obtain a reference to specific type t_ip_mon_data_payload_s by the source that produces it
my_data = t.all.DATA.data_field_by_type_of('myip.mymon.dataport')
# Query for only records of this type, and add it as a field in the results
q = fields(t.all.TIME, t.all.PAYLOAD_TYPE, t.all.SOURCE, t.all.DATA, output_field('MY_DATA', my_s1)).where(t.all.SOURCE == 'myip.mymon.dataport')
results = fetch(q)
```

* To access struct or union fields, dot notation can be used. For example to access `addr` member array of t_ip_mon_cmd_payload_s struct `rec.MY_DATA.cmd.addr`.

* To access array elements or ranges, you can use square brackets. For example to access the elements of `addr`  of t_ip_mon_cmd_payload_s struct `rec.MY_DATA.cmd.addr[0]` or `rec.MY_DATA.cmd.addr[2:0]`. These indexing and slicing notations can also be used to access bits of any packed struct or union. For example `rec.MY_DATA.cmd[1:0]` accesses the first 2 bits of the first member of `cmd` member.

* To retrieve the number of elements in an array or the number of bits in a packed struct/union the `element_count()` method can be used. For example, `rec.MY_DATA.cmd.addr.element_count()` will return the number of elements in the array, and `rec.MY_DATA.cmd` will return the number of bits used for t_ip_mon_cmd_payload_s struct.

* To retrieve the mnemonic of an enum-typed value as a string the `enum_name()` method can be used. For example, `rec.MY_DATA.cmd.cmd.enum_name()` will return the decoded symbolic name of the enum value.

* To convert any SystemVerilog integral data to a Python native `int` the `to_uint()` method can be used. By default, it will throw an exception if the data contains 'x' or 'z' values. However, you can set the `x_to_0` parameter to `True` to convert 'x' values to 0. For example, `rec.MY_DATA.data[0].to_uint(x_to_0=True)`.

* To check if the payload contains 'x' or 'z' values the `is_unknown()` method can be used. For example `rec.MY_DATA.data[0].is_unknown()` will return `True` if the data[0] logic array contains any 'x' or 'z' values.

* (Requires Jem version >= 24.3.1) To determine the underlying type of a value the methods `is_struct()`, `is_union()`, `is_array()`, `is_enum()` and `is_packed()` can be used. Struct, union and array are mutually exclusive, while and value can also be packed. Enums would return true on both `is_enum()` and any underlying type, for example an enum with an underlying type of a packed bit array would return true for both `is_enum()` and `is_array()`.

* The `str(<payload>)` function returns the raw contents of the payload as a string. This can be useful for debugging purposes. However, please note that the format of the string is the tool's internal implementation detail and is subject to change without notice. **DO NOT parse these strings to retrieve data programmatically.**

* The `repr(<payload>)` function returns an internal string representation of the payload. **This string is not usable and should not be relied upon for any operations.**


## 6.13. Constructing queries on Jem trace

Queries on Jem trace are constructed in the same manner as on other UTDB traces. Here is an example of a simple query to obtain all data in chronological recording order:

``` py
trace = connect(...)
q = from_(trace)
for rec in fetch(q):
    print(rec)
```

The above example fetches all the records and prints them. The fetched records will have four fields, according to the schema described above: **TIME**, **PAYLOAD_TYPE**, **SOURCE**, and **DATA**. The values of the **DATA** field will be objects resembling the SystemVerilog types stored in the trace. This is exactly the same structures as used with other methods of Jem trace post-processing. Struct-members and array-elements of the *rec.DATA* value may be accessed using a SystemVerilog-like syntax. For example, consider the SystemVerilog payload type declared as follows:

``` py
typedef struct
{
    bit n1;
    logic [3:0] n2 [1:0];
} t_nested_struct;
 
typedef struct
{
    int f1;
    t_nested_struct f2 [1:0];
} t_my_struct;
```

Then, the following examples are all legal ways to access pieces of the data from the trace:

``` py
trace = connect(...)
q = from_(trace)
for rec in fetch(q):
    # Prints the 4-tuple of the whole record
    print(rec)
    # Prints the DATA field as a SystemVerilog type
    print(rec.DATA)
    # Prints the int member f1
    print(rec.DATA.f1)
    # Prints the 2-bit logic value as specified by the SystemVerilog-like expression
    print(rec.DATA.f2[0].n2[1][1:0])
```

Note that the **DATA** field of a Jem trace usually contains values of different data types, originating from different sources in the simulation model. Therefore, the code accessing the DATA element of the fetched records might need to be more involved. For example, accessing certain members of the structure depending on the **PAYLOAD_TYPE** of the fetched record may look like follows:

``` py
trace = connect(...)
q = from_(trace)
for rec in fetch(q):
    if rec.PAYLOAD_TYPE == 't_my_struct':
        # Prints the int member f1
        print(rec.DATA.f1)
```

The fields **TIME**, **PAYLOAD_TYPE** and **SOURCE** of a Jem trace may be utilized in a usual way, like any other field, to construct more complex queries. For example, the following query would return values originating only from sources matching the given wildcard:

``` py
t = connect(...)
q = where(match(t.all.SOURCE, "soc_top.*.myip*.mymon.myport", kind="wildcard"))
for rec in fetch(q):
    print(rec)
```

### 6.13.1 The nature of the DATA field
The **DATA** field of Jem traces is somewhat special, compared to all other UTDB fields. Since different data sources (e.g. hw-monitors) send out payloads of different data types, this field does not have a single pre-defined datatype, but may contain values of different types. In database parlance this is called a VARIANT field. In standard programming languages, including SystemVerilog, this can be thought of as a "tagged union": a datatype used to hold a value that could take on several different, but fixed, types. Only one of the types is in use in each specific record.

Consider the example trace that contains values of the following unrelated SystemVerilog structs:

``` py
typedef struct packed
{
    bit n1;
    logic [3:0] n2;
} t_struct1;
 
typedef struct
{
    int f1;
    int f2 [1:0];
} t_struct2;
```

In some records of the trace the **DATA** field would contain values of type t_struct1, and in some other records it would contain values of type t_struct2. Sometimes, when constructing simple queries, this fact doesn't matter. For instance, certain basic operations may be applied on the **DATA** field directly, without taking care about the specific type of the value in each record. For example, conversion to string is a valid operation on any value of any datatype, and therefore may be applied on the **DATA** field directly:

``` py
t = connect(...)
strfield = output_field("MYSTR", to_str(t.all.DATA))
q = fields(t.all.TIME, t.all.PAYLOAD_TYPE, t.all.SOURCE, t.all.DATA, strfield)
dump(q)

# Example output:
# TIME | PAYLOAD_TYPE | SOURCE             | DATA                       | MYSTR                     
# ==================================================================================================
#   10 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxxxx, n1 : 0 }   | { n2 : 4'bxxxx, n1 : 0 }  
#   15 | t_struct2    | myip.mymon.myport2 | { f1 : 1, f2 : [ 3, 0 ] }  | { f1 : 1, f2 : [ 3, 0 ] } 
#   20 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxxx1, n1 : 1 }   | { n2 : 4'bxxx1, n1 : 1 }  
#   25 | t_struct2    | myip.mymon.myport2 | { f1 : 2, f2 : [ 6, 3 ] }  | { f1 : 2, f2 : [ 6, 3 ] } 
#   30 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxx10, n1 : 0 }   | { n2 : 4'bxx10, n1 : 0 }  
#   35 | t_struct2    | myip.mymon.myport2 | { f1 : 3, f2 : [ 9, 6 ] }  | { f1 : 3, f2 : [ 9, 6 ] } 
#   40 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bx101, n1 : 1 }   | { n2 : 4'bx101, n1 : 1 }  
```
As can be seen, the values of MYSTR in the example above are exactly identical to the way **DATA** is printed out and it is of different type in different records. The point of this example is that this result was achieved disregarding the specific SystemVerilog types present in the trace.

For more advanced queries, it is often required to work with specific SystemVerilog types. The **data_field_by_type_of()** method may be used to obtain a specifically-typed field by the name of a source that produced such type in the trace. The argument to this method is the source name of interest, or a wildcard that resolves to sources that produce the same SystemVerilog type. (The wildcards are useful, for example, to abstract away that part of the source RTL path where an IP is instantiated, and only focus on the path internal within the IP.) In the example trace above, the values originating from some myip.mymon.myport1 are of SystemVerilog type t_struct1. The following example obtains the field of that specific type and uses it in a query:

``` py
# Obtain a reference to specific type t_struct1 by the source that produces it
my_s1 = t.all.DATA.data_field_by_type_of("myip.mymon.myport1")
q = fields(t.all.TIME, t.all.PAYLOAD_TYPE, t.all.SOURCE, t.all.DATA, output_field("MY_S1", my_s1))

dump(q)
# Example output:
# TIME | PAYLOAD_TYPE | SOURCE             | DATA                       | MY_S1                   
# ================================================================================================
#   10 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxxxx, n1 : 0 }   | { n2 : 4'bxxxx, n1 : 0 }
#   15 | t_struct2    | myip.mymon.myport2 | { f1 : 1, f2 : [ 3, 0 ] }  |                         
#   20 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxxx1, n1 : 1 }   | { n2 : 4'bxxx1, n1 : 1 }
#   25 | t_struct2    | myip.mymon.myport2 | { f1 : 2, f2 : [ 6, 3 ] }  |                         
#   30 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxx10, n1 : 0 }   | { n2 : 4'bxx10, n1 : 0 }
#   35 | t_struct2    | myip.mymon.myport2 | { f1 : 3, f2 : [ 9, 6 ] }  |                         
#   40 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bx101, n1 : 1 }   | { n2 : 4'bx101, n1 : 1 }
#   45 | t_struct2    | myip.mymon.myport2 | { f1 : 4, f2 : [ 12, 9 ] } |                         
#   50 | t_struct1    | myip.mymon.myport1 | { n2 : 4'hA, n1 : 0 }      | { n2 : 4'hA, n1 : 0 }   
#   55 | t_struct2    | myip.mymon.myport2 | { f1 : 0, f2 : [ 0, 12 ] } |                         
#   60 | t_struct1    | myip.mymon.myport1 | { n2 : 4'h5, n1 : 1 }      | { n2 : 4'h5, n1 : 1 }   
```

In the above example, my_s1 is an expression of the specific SystemVerilog type t_struct1. In all records where the value of the **DATA** field is indeed of type t_struct1, my_s1 evaluates to that same value. In all other records, it evaluates to null, as shown in the example output of that query.  The my_s1 expression represents the SystemVerilog type exactly as coded in the SystemVerilog source code. Struct members and array elements may be accessed using SystemVerilog-like syntax:

``` py
# Obtain a reference to specific type t_struct1 by the source that produces it
my_s1 = t.all.DATA.data_field_by_type_of("*myip.mymon.myport")

# And use it in a query
q = from_(t).where(my_s1.n2[1] == 0)

dump(q)
# Example output:
# TIME | PAYLOAD_TYPE | SOURCE             | DATA                     | MY_S1                   
# ==============================================================================================
#   40 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bx101, n1 : 1 } | { n2 : 4'bx101, n1 : 1 }
#   60 | t_struct1    | myip.mymon.myport1 | { n2 : 4'h5, n1 : 1 }    | { n2 : 4'h5, n1 : 1 }   
#   80 | t_struct1    | myip.mymon.myport1 | { n2 : 4'h5, n1 : 1 }    | { n2 : 4'h5, n1 : 1 }   
```

Note that the output of the above example only contains records where **DATA** field is of type t_struct1. This is because my_s1 evaluates to null in all other records, making the whole condition inside **where()** have a null value (which is considered false truth value).

Another way to obtain a specifically-typed field is by using the **data_field_by_port_and_type()** method. It accepts two string arguments: the name of a hw-monitor port and the name of the type that port transfers. This combination is guaranteed to uniquely identify a specific SystemVerilog type in a given trace by Jem methodology. (Type names themselves are not guaranteed to be unique!)

``` py
# Obtain a reference to specific type t_struct1 by the port-name/type-name pair
my_s1 = t.all.DATA.data_field_by_port_and_type("myport", "t_struct1")

# And use it in a query
q = from_(t).where(my_s1 == 0)
```

Given the ability to obtain fields of specific SystemVerilog types, these expressions may be used similarly to all other UTDB expressions: constructing conditions to filter the trace, to select only a subset of information to retrieve, etc. These expressions may be converted to native types using the standard UTDB cast operators **to_str()**, **to_uint()**, etc. Integral SystemVerilog types may be used in numeric expressions without casting. There is also a number of special built-in functions available for specific purposes.

### 6.13.2 Additional considerations and examples
***Figuring out all source names in Jem trace***
It is possible to obtain a list of all source names for a given trace using **sources()** method:

``` py
t = connect(...)

all_sources = t.all.DATA.sources()
print(all_sources)
# Example output:
# ['myip.mymon.myport2', 'myip.mymon.myport3', 'myip.mymon.myport1']
```

***Use output_field() to give names to complex expressions in query result***
The specifically-typed fields obtained from **data_field_by_type_of()** and **data_field_by_port_and_type()**, as well as any member/array-select from them, do not have pre-defined names. If such an expression is desired to be part of a query result, it cannot be used in **fields()** as-is. Instead, **output_field()** should be used to give a name to such expression in the query result.
The following example combines computed fields, expressions over SystemVerilog types, and **where()** to produce a filtered result with five fields: **TIME**, **SOURCE**, **CMD**, **SEGMENT** and **OFFSET**:

``` py
t = connect(...)
my_s = t.all.DATA.data_field_by_type_of("*.a.b.p")
 
fcmd = output_field("CMD", my_s.cmd)
fseg = output_field("SEGMENT", my_s.addr[16:8])
foff = output_field("OFFSET", my_s.addr[7:0])
 
q = fields(t.all.TIME, t.all.SOURCE, fcmd, fseg, foff).where(my_s.addr[7:2] > 100)
```

***Values in Jem traces may contain X-es***
The 'x/'z values (collectively termed "unknown values") may occur naturally in Jem traces, where the corresponding SystemVerilog type was a 4-state type. The built-in function **is_unknown()** may be used to explicitly check if a value contains any unknown bit; it is analogous to SytemVerilog standard $isunknown() function. Whenever a SystemVerilog type needs to be converted to an integer value, the result will be null if there are unknown bits. The unknown bits may be instead converted to 0 by explicitly casting the SystemVerilog value to an integer using the built-in functions **to_uint()** and alike with x_to_0 argument set to True.

``` py
t = connect(...)
my_s1 = t.all.DATA.data_field_by_type_of("*myip.mymon.myport")

# Show value of t_struct1.n2 converted to uint with and without x-to-0
my_s1_n2 = output_field("MY_S1_N2", to_uint(my_s1.n2))
my_s1_n2_x_to_0 = output_field("MY_S1_N2_X_TO_0", to_uint(my_s1.n2, x_to_0=True))

q = fields(t.all.TIME, t.all.PAYLOAD_TYPE, t.all.SOURCE, t.all.DATA, my_s1_n2, my_s1_n2_x_to_0)
q = q.where(t.all.PAYLOAD_TYPE == "t_struct1")

dump(q)

# Example output:
# TIME | PAYLOAD_TYPE | SOURCE             | DATA                     | MY_S1_N2 | MY_S1_N2_X_TO_0
# ================================================================================================
#   10 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxxxx, n1 : 0 } |          |               0
#   20 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxxx1, n1 : 1 } |          |               1
#   30 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bxx10, n1 : 0 } |          |               2
#   40 | t_struct1    | myip.mymon.myport1 | { n2 : 4'bx101, n1 : 1 } |          |               5
#   50 | t_struct1    | myip.mymon.myport1 | { n2 : 4'hA, n1 : 0 }    |       10 |              10
#   60 | t_struct1    | myip.mymon.myport1 | { n2 : 4'h5, n1 : 1 }    |        5 |               5
#   70 | t_struct1    | myip.mymon.myport1 | { n2 : 4'hA, n1 : 0 }    |       10 |              10
#   80 | t_struct1    | myip.mymon.myport1 | { n2 : 4'h5, n1 : 1 }    |        5 |               5
#   90 | t_struct1    | myip.mymon.myport1 | { n2 : 4'hA, n1 : 0 }    |       10 |              10
```
As can be seen in the example output, MY_S1_N2 has null values in records where there are 'x-es.

***Working with SystemVerilog enum types***
Information about enum types coming from SystemVerilog is preserved inside Jem traces. Consider the following SystemVerilog type:
``` py
typedef struct
{
  enum { RED, GREEN, BLUE } color;
}
t_struct3;
```

A trace containing such values could look like:

``` py
t = connect(...)
q = where(t.all.PAYLOAD_TYPE == "t_struct3")

dump(q)
# Example output:
# TIME | DATA                | PAYLOAD_TYPE | SOURCE            
# ==============================================================
#   10 | { color : RED 0 }   | t_struct3    | myip.mymon.myport3
#   20 | { color : GREEN 1 } | t_struct3    | myip.mymon.myport3
#   30 | { color : BLUE 2 }  | t_struct3    | myip.mymon.myport3
#   40 | { color : RED 0 }   | t_struct3    | myip.mymon.myport3
```

The above example shows that the string representation of enum values, as produced by **dump()** or **to_str()**, includes both the numeric value and the mnemonic of the enum value. It is possible to obtain the mnemonic alone using the built-in function **enum_name()**, as shown in the following example:

```
t = connect(...)
my_s3 = t.all.DATA.data_field_by_type_of("myip.mymon.myport3")

as_num = output_field("AS_NUM", to_uint(my_s3.color))
as_name = output_field("AS_NAME", enum_name(my_s3.color))
as_str = output_field("AS_STR", to_str(my_s3.color))

q = fields(t.all.TIME, t.all.DATA, as_num, as_name, as_str).where(my_s3.color > 0)

dump(q)
# Example output:
# TIME | DATA                | AS_NUM | AS_NAME | AS_STR 
# =======================================================
#   20 | { color : GREEN 1 } |      1 | GREEN   | GREEN 1
#   30 | { color : BLUE 2 }  |      2 | BLUE    | BLUE 2 
#   50 | { color : GREEN 1 } |      1 | GREEN   | GREEN 1
#   60 | { color : BLUE 2 }  |      2 | BLUE    | BLUE 2 
#   80 | { color : GREEN 1 } |      1 | GREEN   | GREEN 1
#   90 | { color : BLUE 2 }  |      2 | BLUE    | BLUE 2 
```

It is also possible to use the enum literals - the named constants themselves. They are obtained as members of enum-typed expressions. The following example shows the constant BLUE from the enum type of t_struct3.color used in the **where()** condition:

```
t = connect(...)

my_s3 = t.all.DATA.data_field_by_type_of("myip.mymon.myport3")
q = fields(t.all.TIME, t.all.DATA).where(my_s3.color == my_s3.color.BLUE)

dump(q)
# Example output:
# TIME | DATA              
# =========================
#   30 | { color : BLUE 2 }
#   60 | { color : BLUE 2 }
#   90 | { color : BLUE 2 }
```

***Retrieving a list of struct/union members***
It is possible to obtain a list of all members for a given struct or union using **list_members()** method.
This method returns a dictionary with the member names as key, and a reference to the member which can be used in the query or output fields construction.
This method returns an empty dictionary when invoked on non struct/union selection for a Jem DATA field.

``` py
# Obtain a reference to specific type t_struct1 by the source that produces it
my_s1 = t.all.DATA.data_field_by_type_of("myip.mymon.myport1")

# Retrieve a list of members of the struct defined for my_s1 payload type
members = my_s1.list_members()

# Construct output fields for each member of the struct
my_fields = [output_field("MY_"+m_key.upper(), m_ref) for m_key, m_ref in members.items()]

# And use them in a query
q = from_(t).where(t.all.SOURCE == "myip.mymon.myport1").fields(t.all.TIME, *my_fields)

dump(q)
# Example output:
# TIME | MY_N1 | MY_N2   
# ==============================
#   40 | 1     | 4'bx101 
#   60 | 1     | 4'h5    
#   80 | 1     | 4'h5    

```

***Retrieving the number of elements in an array***
It is possible to obtain the number of elements (size) in an array defined in a given payload type using **element_count()** method.
This method can also be invoked for a packed struct/union, the returned value will be the number of bits in the bit array representation of the packed struct/union.
This method returns 0 when invoked on any non array or packed struct/union selection for a Jem DATA field.

``` py
# Obtain a reference to specific type t_struct1 by the source that produces it
my_s1 = t.all.DATA.data_field_by_type_of("myip.mymon.myport1")
my_s2 = t.all.DATA.data_field_by_type_of("myip.mymon.myport2")

# Retrieve sizes of t_struct1.n2 and t_struct2.f2 arrays
print("Size of t_struct1.n2 array: ", my_s1.n2.element_count())
print("Size of t_struct2.f2 array: ", my_s2.f2.element_count())

# Example output:
# Size of t_struct1.n2 array: 4
# Size of t_struct2.f2 array: 2
```

----
# 7 UTDB Views
UTDB View are in many ways very much like a UTDB Trace. It has metadata with record types and fields that can be used for constructing queries on top of the View.

A View is constructed by using queries that were defined on some Trace or another View. There are 2 methods for creating a View:

* **view()** method is used with a single query to create a view that represents the results of the query.
* **union_view()** method is used with multiple queries (or views) to create a view that represents the aggregated results of all the queries.

***Note:***
- The result of sub-query/view of **union_view()** may be hierarchical, i.e. contains the parent-child relationships, or flat, i.e. does not contain or ignores the parent-child relationships between the records.
- If all sub-queries of **union_view()** are hierarchical, the result will also have hierarchical structure and will keep parent-child relationships of the source data.

Views can be very useful for simplifying complex queries and to create on-the-fly multiple queries aggregations. In addition, View can be stored (using **store()** method) to create UTDB in the file system.

``` py

# Example #1
# define view with subset of fields and additional field representing the name of original tracker
v1 = view(fields(output_field("TRACKER", "trace1"), trace1.all.TIME, trace1.all.OPCODE).where(trace1.all.TIME > 3000))
 
# filter results of view
q = where(v1.all.OPCODE.contains('Cmp')).limit(3,-5)
 
# Example #2
# define view and rename original record types
q1 = fields(output_field("TRACKER", "trace1")).fields(trace1.all.TIME, trace1.all.OPCODE, trace1.all.ADDRESS, trace1.all.OPCODE).where((trace1.all.TIME < 1100) | (trace1.all.TIME > 3000))
v1 = view(q1,  rename_record_types = {trace1.cpurequest : 'foo', trace1.nbrequest : 'xyz'})
 
# filter results of record type ‘xyz’ in view
q2 = from_(v1).where(v1.xyz.OPCODE == "Write")
 
# Example #3
# define union_view from two views when each view has record_type ‘cpurequest’ which has different definition
trace1 = connect(…)
trace2 = connect(…)
 
v1 = view(fields(output_field("TRACKER", "trace1")).fields(trace1.all.TIME, trace1.all.OPCODE))
 
v2 = view(fields(output_field("TRACKER", "trace2")).fields(trace2.all.TIME, trace2.all.OPCODE),  rename_record_types = {trace2.cpurequest : 'abc'})
 
uv = union_view(v1, v2, sort_by= [ ("TIME", ASC) ])
 
# filter results of union view with records of record type ‘abc’
q = fields(uv.all.TIME, uv.all.TRACKER, uv.all.OPCODE).where(uv.abc.OPCODE == "Read") 

```

---
# 8 UTDB Flow Detection
Flow detection is used to find behaviors of events in system under test. For that matter we can consider an Event to be a record in UTDB Trace and a Flow to define some behavior of multiple events in the system.

## 8.1 Basic flow elements
Flow represents some temporal relationship between multiple events (records) and lookaheads in the Trace. It can also have a name for easier readability of the flow detection results.

Event represents a boolean expression matching one or more records in the Trace. It can also have a name for easier readability of the flow detection results.

A Lookahead represents a boolean expression, but does not match to a record in the trace. Instead, it matches at a point between records and asserts that the consecutive record satisfies the boolean expression.

There are flow construction methods to define the temporal relations between multiple events:

* **seq()** – means that its parameters will occur in a sequential order in the flow.
* **one_of()** - means that only one of its parameters will occur in the flow.
* **all_of()** - means that all its parameters will occur in the flow with no particular order.
* **repeat()** - means that the first operand will be repeated within given boundaries and until a provided condition is fulfilled.

``` py

# simple boolean expression event definition
e1 = trace.all.OPCODE == 'Write'
 
# simple event object definition
e1 = event(trace.all.OPCODE == 'Read')
 
# simple event object definition with user defined name
e3 = event(trace.all.OPCODE == 'Check', name='check')
 
# lookahead object definition
la1 = lookahead(trace.all.OPCODE == 'Cmp', name='cmp')
 
# expect sequential order of the above events and user defined name
f1 = seq(e1, e2, la1, e3, name='mem_seq')
 
# expect occurrence of only one the events
f2 = one_of(e1, e2, e3)
 
# expect occurrence of all the events with no particular order
f3 = all_of (e1, e2, e3)
 
# use nested flow definition (sequence of all_of and e3)
f4 = seq(all_of(e1, e2), la1, e3)
 
# flow with other flow objects and boolean expression with no particular order
f4 = all_of(f1, trace.all.OPCODE == 'RegWrite')
 
# repeat f1 between 3 and 5 times until some condition is fulfilled
f5 = repeat(f1, min=3, max=5, until=trace.all.OPCODE == 'RegWrite')

```
## 8.2 Flow elements repetitions
Flow elements repetitions enable definition of multiple occurrences of an element in the flow. The slicing operator [] is used to define multiple occurrences of an element in a flow.

The following table describes the supported repetition expression values:

| Expression | Description |
| ---------- | ----------- |
| **[x]**   | Exactly x repetitions |
| **[x:y]** | Between x and y repetitions |
| **[x:]**  | Between x and any number of times |
| **[:y]**  | Between 0 and y times |
| **['*']** | Between 0 to any number of times |
| **['+']** | Between 1 to any number of times **[1:]** |
| **['?']** | 0 or one times **[:1]** |

***Code Example:***

``` py

e1 = event()
e2 = event()
e3 = event()
e4 = event()
 
# flow that detects sequential order of elements include repetitions
#   2 repetitions of e2
#   0 to 3 repetitions of e3
flow = seq(e1, e2[2:2], e3[:3], e4)
 
```

## 8.3 Flow abort parameter
Flow abort parameter enables setting some condition that will abort the flow detection process and ignore the detected events for the flow. This is done by setting flow construction method parameter abort.

***Code Example:***

``` py

e1 = event()
e2 = event()
e3 = event()
e4 = event()
 
# flow that detects sequential order of elements and abort if e4 is detected after the flow started and before it ended
flow = seq(e1, e2, e3, abort=e4)

```

## 8.4 Flow Variables
Flow variables enable storing and using data across multiple events in the flow. This enables more specific relation between events that is based on their data and not only their order.

Definition or reference to a Flow variable is done by using *var()* method and giving the unique name of the variable. Setting or using Flow variable is done in the context of an Event object using the Event’s creation method *test_or_set* and **assign** parameters or as part of some UTDB value or Boolean expression.

variable can also be assigned to a python variable so the python variable can be used in the code instead of explicitly using the **var()** method when using test_or_set or assign on the same variable in multiple events in the flow.

***Code Example:***

``` py

# event creation using test_or_set 'coreid' inline flow variable
e3 = event(…, test_or_set={ var('coreid'): trace.all.COREID })
 
# event creation using test or set 'cpureq' python flow variable
cpureq = var('cpureq')
e4 = event(…, test_or_set={ cpureq: trace.all.CPUREQID} )
 
# using python 'cpureq' flow variable in event condition expression
e5 = event(trace.all.CPUREQID == cpureq)

```

## 8.4.1 assigning values Flow Variables in events  
The flow element **assign** parameter accepts a dictionary of key-value pairs where the key expressions are Flow Variables and the value expressions are any UTDB expressions that can be evaluated to a value in the context of a matched event.

The variable will be assigned the value evaluated from the expression immediately following the matching of the event.

## 8.4.2 testing or setting Flow Variables in events
The **test_or_set** parameter accepts a dictionary of key-value pairs where the key expressions are Flow Variables and the value expressions are any UTDB expressions that can be evaluated to a value in the context of a matched event.

The **test_or_set** logic is:
* If the *variable is not set*, the variable will be assigned with a corresponding expression value following the matching of the event.
* If the *variable is already set*, the event will only be matched if the value set to the variable is equal to the value evaluated from the expression.

## 8.5 Flow Detection Query and results
The basic flow detection query is created by using the **detect()** query method and providing the flow that needs to be detected. The **fetch()** method is used to execute the query and obtain the results.

The **detect()** method also accepts flow detection output, mode parameters and measures that are discussed in detail in the API reference section.

The returned Results of detect query is built out of top-level flow occurrence records.

***The flow occurrence record has the following built-in fields:***

* **RECORD_TYPE** – value is set to built-in record type **utdb_match**
* **UTDB_CHILDREN** – is a list containing the event (or other flow elements) records that were detected for the flow occurrence, and additional records of the next expected events that were not matched in an incomplete flow occurrence.

***Code Example:***

``` py

# flow query
flow_q = detect(seq(..., name='flow1'))
 
# get flow query results
results = fetch(flow_q)
 
# access query results
for flow_oc in results:
    print(flow_oc.RECORD_TYPE + ':')
    for e in flow_oc.UTDB_CHILDREN:
        print(e)
 
'''
printed results example
utdb_match:
(TIME=1234, OPCODE='WRITE', ...)
'''

```
## 8.6 Flow Detection Measures
Measures are additional fields computed during detect query execution and added to results. A Measure consists of measure name that will be the field name in results under which the Measure is reported, and the expression which will be evaluated to its value for each row. Expressions that cannot be evaluated to a literal value (e.g flow definitions) cannot be used as the measure expression. An optional keyword argument **format** can be added with python formatting string to measure definition. Format string is used to set the string representation of the fields values in dump API and GUI.

The Measure expression is evaluated for each row in the results. If a measure cannot be evaluated for a given row, for example if it uses the value of a field that does not exist for the matched row, the value of the measure for that row will be set to NULL.

Built-in measure functions extract match-specific data that cannot be used elsewhere in expressions, but can be reported using measures.
* **match_name()** - evaluated to event/flow name of the match.
* **match_status()** - evaluated to completion status of flow (**COMPLETE**/**INCOMPLETE**), and match status of events (**MATCHED**/**EXPECTED**).
* **match_flow_type()** - evaluated to flow type used (seq, one_of, all_of, repeat) and event type (event or lookahead)

***Code Example:***

``` py

# measures
m_1 = measure('M_RELATIVE_TIME', trace.all.TIME - 1200) # user defined measure
m_2 = measure('FULL_ADDRESS', trace.all.OFFSET + trace.all.ADDRESS, format='0x{:016X}') # user defined measure with display formatting
m_name = measure('UTDB_MATCH_NAME', match_name()) # built-in name measure
m_status = measure('UTDB_MATCH_STATUS', match_status()) # built-in status measure
m_flow_type = measure('UTDB_MATCH_FLOW_TYPE', match_flow_type()) # built-in flow_type measure
 
#flow query
flow_q = detect(seq(..., name='flow1', measures=[m_1, m_name, m_status, m_flow_type]))
 
# get flow query results
results = fetch(flow_q) 

```

---
# 9 UTDB Coverage Collection
Coverage collection API elements are taken from other coverage definition environments and include Covergroups, Coverpoints, Cover Bins and Cross coverage. Covergroup is a container with a name, instance name (optionally), and one or more Coverpoints. Coverpoint is some element of an item that requires coverage monitoring. Cover Bin is a bucket of one or more values we want to get the count for. Cross coverage is cross product of multiple bins and/or Coverpoints.

Covergroups' and Coverpoints' definitions are stored with their location (file name and line number) for future viewing of the original source code in EDA coverage analysis tools. File name and line number associated with coverage definition are extracted automatically when **covergroup()**/**coverpoint()** method is called or may be provided by user in the **location** attribute of the **covegroup()**/**coverpoint()** methods.    

See more details below and in the API reference section.

## 9.1 Define Covergroup
Covergroup is a container of Coverpoints and crosses. The global method **covergroup()** is used to create a new Covergroup object, and it requires a name as a parameter. If multiple instances of a covergroup exist, the **instance** attribute should be provided to enable per-instance coverage collection. The merging of coverage from all instances into the covergroup coverage is done automatically by EDA coverage analysis tools.

Covergroup method **covepoints()** returns the list of Coverpoints objects defined in this Covergroup.

``` py

# create new coverage group object
cg1 = covergroup('Cg1')

cg2_1 = covergroup('Cg2', instance="a.b.c[1].Cg2")
cg2_2 = covergroup('Cg2', instance="a.b.c[2].Cg2")
cg2_2 = covergroup('Cg2', instance="a.b.c[3].Cg2")

```

## 9.2 Define Coverpoint and Bin
Coverpoint defines an element that will be monitored using the Covergroup **coverpoint()** method, and the values to count using the Coverpoint **bin()** methods. Coverpoint has a **name** attribute and other attributes based on the type of the Coverpoint. Bin also has a name and the one or more values to count for that bin.

***UTDB API support 3 types of Coverpoint:***

* Value Coverpoint – monitor and count values of some utdb value expression
* Sampled Coverpoint – let the user do the value sampling while UTDB does the coverage counting
* Query Coverpoint – monitor and count results of utdb parameterized query

***UTDB API supports 3 methods to define Coverpoint bins:***

* **bin()** method – to create a single Bin that can count hits for one or more values
* **bin_per_value()** - to create a Bin array that counts hits for each value in the array (for value-coverpoint) or for each combination of parameter values (for query-coverpoint)
* automatic bin generation – automatically breaks integral ranges into bins

**ignore()** method is used to specify values that should be excluded from all Coverpoint’s bins.

Below is more info of how to create each Coverpoint type and the bins for these Coverpoints.

### 9.2.1 Value coverage point
Value Coverpoint monitors a utdb value expression and counts how many times values are seen for that expression. The expression is defined by setting the values_of parameter of the coverpoint method.

***Other parameters that can also be set:***

* **iff** – a boolean utdb expression, used to ignore some trace records.
* **collect** – a boolean value. If the value is False, the coverage data will not be collected by the Coverpoint itself, but it can be used as an element for cross definition.

``` py

# create Covergroup
cg1 = covergroup('my_cover_group')
 
# create uop value Coverpoint for cg1 Covergroup
uop_cp = cg1.coverpoint('uop', values_of=trace.all.UOP)
 
# create address value Coverpoint for cg1 Covergroup only for WRITE uop
addr_cp = cg1.coverpoint('addr', values_of=trace.all.ADDR,
           iff=trace.all.UOP == 'WRITE')

```

In addition, a set of bins can be defined specifying the expression value buckets that need to be counted and specific values that may be ignored from all bins.

``` py

# define set of bins for each uop value in the list
all_uop_bins = uop_cp.bin_per_value('uops', ['READ', 'WRITE', 'MODIFY'])
 
# this will create bin and count the hits of each value in the list.
# results example:
# bin name   # hit count
uops[READ]   8
uops[WRITE]  3
uops[MODIFY] 10
 
# define single bin for uop modifiers value set
mod_uops = uop_cp.bin('mod_uops', ['WRITE', 'MODIFY'])
 
# this will create single bin and count both WRITE and MODIFY value hits.
# results example:
# bin name   # hit count
mod_uops     13 # sum of WRITE and MODIFY hits
 
# define automatic bins for address space
addr_bins = addr_cp.auto_gen_bin('addr')
 
# this will create 64 bins and split the address space to 64 parts evenly
# results example:
# bin name   # hit count
addr[0:0x01FFFFFF]     13
addr[0x01FFFFFF:0x02FFFFFF]     14
...
 
# Example with  ignore
# define set of bins for each uop value in the list
all_uops = uop_cp.bin_per_value('uop', ['READ', 'WRITE', 'MODIFY', ‘ADDEND’])
 
# define single bin for uop modifiers value set
mod_uops = uop_cp.bin('mod_uops', ['WRITE', 'MODIFY', ‘APPEND’])
 
# ignore ‘APPEND’ value
uop_cp.ignore([‘APPEND’])
 
# ‘APPEND’ is ignored from both, all_uops and mod_uops, bins and does not appear in # results
# results example:
# bin name  # hit count
uop[READ]   8
uop[WRITE]  3
uop[MODIFY] 10
mod_uops    13 # sum of WRITE and MODIFY hits

```
### 9.2.2 Sampled coverage point
Sampled Coverpoint is used for collecting coverage data, based on user values sampling. Sampled Coverpoint has a name and the type of the values that are going to be sampled.

***Other parameters that can also be set:***

* **collect** – boolean value. If the value is False, the coverage data will not be collected by the Coverpoint itself, but it can be used as an element for cross definition.

In addition, it is mandatory that Sampled Coverpoint will have user defined bins. (see later in this chapter) and the sampled values are compared against the defined bins.

``` py

# create Covergroup
cg1 = covergroup('my_cover_group')
 
# create data sampled value Coverpoint for cg1 Covergroup
data_cp = cg1.coverpoint('data', value_type=DataType.INT)

```
In addition, a set of bins must be defined specifying the value buckets that needs to be counted.

``` py
# define set of bins for each uop value in the list
data_bins = data_cp.bin_per_value('data', [range(0x00,0x10), range(0x10,0x20),…, range(0xE0,0x100)])
 
# this will create bin and count the hits of each range in the list.
# results example:
'''
bin name          hit count
data[0x00,0x10]  = 8
data[0x10,0x20]  = 4
…
data[0xE0,0x100] = 4
'''
 
# define single bin for low data values
low_data = data_cp.bin('low_data', range(0x00,0x80))
 
# this will create single bin and count hits for values range from 0 to 0x7F.
# results example:
'''
bin name         hit count
low_data       = 20 # sum of hits for data between 0 and 0x7F
'''

```
### 9.2.3 Query coverage point
Query Coverpoint monitors a utdb query and counts the number of items present in a query result. The query argument is any query constructed using the query API.  Such query may be parameterized or not.  When a parameterized query is used in query-coverpoint, bins must be explicitly specified. The coverage space is defined by the values of the parameters. In other words, bins count how many items are present in the query result for given combinations of parameter values.

***Other parameters that can also be set:***

* ***collect*** – boolean value. If the value is False, the coverage data will not be collected by the Coverpoint itself, but it can be used as an element for cross definition.

``` py

# create Covergroup
cg1 = covergroup('my_cover_group')
 
# create UOP_x_ADDR query Coverpoint for cg1 Covergroup
uop_addr_cp = cg1.coverpoint( 'UOP_ADDR_CP',
                                query=where((trace.all.UOP.contains(P('uop'), ignore_case=True)) & (trace.all.ADDR == P('addr')))
                            )

```

In addition, a set of bins can be defined specifying the combinations of parameter values that needs to be counted.

``` py

# define set of bins for each pair <uop,addr> of values in the list
uop_addr_bins = uop_addr_cp.bin_per_value('uop_addr',
            {
                P('uop'): ['READ', 'WRITE', 'MODIFY'],
                P('addr') : [0x0000, 0x000F]
            }
)
 
'''
This will create bin and count the hits of each combination.
results example:
bin name                  hit count
uop_addr[READ,0x0000]   = 8
uop_addr[READ, 0x000F]  = 3
uop_addr[WRITE,0x0000] = 0
uop_addr[WRITE,0x000F] = 100
'''
 
# define single bin for all combinations of <uop,addr>
mod_uops = uop_addr.bin('mod_uops', {P('uop'): ['WRITE', 'MODIFY'],
    P('addr'): [0x0012, 0x1234]
   })
 
'''
This will create single bin and count 4 combinations:
[WRITE,0x0012], [WRITE,0x1234], [MODIFY,0x0012], [MODIFY,0x1234]
results example:
bin name     hit count
mod_uops   = 13 # sum of hits of 4 combinations

```

## 9.3 Sample and fetch coverage results
For sampled Coverpoints, the user needs to manually sample values using the Coverpoint **sample()** method and providing the sampled values. For value Coverpoints, the coverage is automatically collected by UTDB when the **fetch_coverage()** method is called. **fetch_coverage()** method collects coverage for one or more Covergroups. If a Covergroup contains sampled Coverpoints, the user needs to do the value sampling before the call to **fetch_coverage()**.

Beyond the mandatory Covergroup list, **fetch_coverage()** has parameters to control the coverage results destination and format as follows:

- ***format*** – format of the data using one of the following:
	- **TEXT** – write coverage data in a readable text format
	- **UCIS** - write coverage data to file in USIS format
	- **VDB** - write coverage data to file in VDB format (Synopsis)
    - **UNICOV** - write coverage data to file in VDB format (Cadence)
	- **RESULT_ITERATOR** – return coverage data in results object
- **output** – output directory (in case of output file)
- **testname** – string that is used for regression level coverage data aggregation
- **module** – string that is used for regression level coverage data aggregation

Using the coverage elements above, the following shows how to sample coverpoint data:

``` py

# manual sampling of data Coverpoint
data_cp.sample(0x00)
data_cp.sample(0xD5)
data_cp.sample(0x7F)
# …

```

Coverage collection to text file example:

``` py

# fetch data coverage results and save to text file
fetch_coverage([cg1], format=CoverageOutputFormat.TEXT)
  
'''
coverage_report.txt coverage text file content example:
Covergroup: Cg1
Coverpoint: uop
uops[READ]      8
uops[WRITE]     3
uops[MODIFY]        10
mod_uops        13
Coverpoint: data # based on sampled data above
    data[0x00..0x0F]    1
data[0x10..0x1F]    0
…
data[0x60..0x6F]    0
data[0x70..0x7F]    1
data[0x80..0x8F]    0
…
data[0xC0..0xCF]    0
data[0xD0..0xDF]    1
data[0xE0..0xEF]    0
…
low_data        2
'''

```
Coverage collection to results object example:

``` py

# fetch data coverage results and save to text file
cov_results = fetch_coverage([cg1], format=CoverageOutputFormat.RESULT_ITERATOR)
 
# read coverage results:
for row in cov_results:
print(row.COVERGROUP_NAME, row.COVERPOINT_NAME, row.BIN_NAME, row.HITCOUNT)
 
'''
results printing example:
Cg1 uop uops[READ] 8
Cg1 uop uops[WRITE] 3
Cg1 uop uops[MODIFY] 10
Cg1 uop mod_uops 13
Cg1 data data[0x00..0x0F]   1
Cg1 data data[0x10..0x1F]   0
…
Cg1 data data[0x60..0x6F]   0
Cg1 data data[0x70..0x7F]   1
Cg1 data data[0x80..0x8F]   0
…
Cg1 data data[0xC0..0xCF]   0
Cg1 data data[0xD0..0xDF]   1
Cg1 data data[0xE0..0xEF]   0
…
Cg1 data low_data 2
'''

```

## 9.4 Define Cross Coverage
Cross coverage generates cross product coverage bins of multiple predefined bins. The Covergroup **cross()** method is used to create a cross object, taking a name and a list of bins or coverpoint objects as parameters.

***Important Note***:
- Cross coverage cannot mix value Coverpoints and sampled Coverpoints. It can only use one of these kinds.
- Cross Coverage that crosses sampled Coverpoints elements is called a sampled cross coverpoint.

For a sampled cross coverpoint object the **ignore()** method is used to specify crossed values that should be excluded from all Coverpoint’s bins.  The parameter of the **ignore()** method is a dictionary from the coverpoint element to list of its excluded values.

For a sampled cross coverpoint object the **sample()** method needs to be called in order to count the hits of the crossed values (based on the Coverpoint value space).

The parameters of the cross coverpoint **sample()** method can be list of values in the order of the parameters to the cross definition, or a dictionary from the coverpoint element to its sampled value. 

***Code example:***

``` py

# define 2 value Coverpoints with bins and no Coverpoint coverage collection
value_cp1 = cg2.coverpoint('vcp1', values_of=trace.all.FIELD1, collect=False)
vcp1_bins = value_cp1.bin_per_value("bin1", ['A', 'B', 'C', 'D'])
 
value_cp2 = cg2.coverpoint('vcp2', values_of=trace.all.FIELD2, collect=False)
vcp2_bins = value_cp2.bin_per_value('bin2', [1, 2, 3])
 
# define 2 sampled Coverpoints with bins and no Coverpoint coverage collection
sampled_cp1 = cg2.coverpoint('scp1', value_type=DataType.STRING, collect=False)
scp1_bins = sampled_cp1.bin_per_value('bin1', ['X', 'Y', 'Z'])
 
sampled_cp2 = cg2.coverpoint('scp2', value_type=DataType.INT, collect=False)
scp2_bins = sampled_cp2.bin_per_value('bin2', [5,6,7])
 
# define cross coverage for the value and sampled Coverpoints/bins
value_cross = cg1.cross('crossF1_F2', value_cp1, vcp2_bins)
sample_cross = cg1.cross('scp2Xscp1', sampled_cp2, sampled_cp1)
# define ignored combinations bin2[5]_x_bin1[X], and bin2[6]_x_bin1[X]
sample_cross.ignore({sampled_cp2: [5,6], sampled_cp1: ['X']})
 
# sample values into sampled cross coverage object using ordered value list (correlated to the order of the Coverpoints in the cross definition)
sample_cross.sample(5, 'Y')
sample_cross.sample(6, 'Y')
sample_cross.sample(5, 'Z')
# sample values into sampled cross coverage object using dictionary fomr cross element to its value
sample_cross.sample({sampled_cp2:7, sampled_cp1:'X'})
sample_cross.sample({sampled_cp1:'Y', sampled_cp2:6})
# …
 
# fetch and store coverage result in text file
fetch_coverage([cg2], format=CoverageOutputFormat.TEXT)
 
'''
coverage text file content example:
Covergroup: Cg2
Cross: F1XF2 # based on utdb query
bin1[A]_x_ bin2[1] 1
bin1[A]_x_ bin2[2] 0
bin1[A]_x_ bin2[3] 4
bin1[B]_x_ bin2[1] 2
bin1[B]_x_ bin2[2] 1
bin1[B]_x_ bin2[3] 2
…
Cross: scp2Xscp1 # based on sampled data above
bin2[5]_x_ bin1[Y] 1
bin2[5]_x_ bin1[Z] 1
bin2[6]_x_ bin1[Y] 2
bin2[6]_x_ bin1[Z] 0
bin2[7]_x_ bin1[X] 1
bin2[7]_x_ bin1[Y] 0
bin2[7]_x_ bin1[Z] 0
'''

```

## 9.5 VDB and UNICOV coverage results
UTDB can generate coverage results in VDB (Synopsys) and UNICOV (Cadence) format.  UTDB does not set any environment needed to run vendors' tools for coverage generating and analysis. We work with versions of Synopsys/Cadence tools defined in project environment. 
The single requirement to user environment from UTDB side – covimport (for VDB) and/or ucis2ucd (for UNICOV) utilities should be available for running from UTDB.

Below are examples of minimalistic environment setup for generating VDB/UNICOV data

``` py

# minimalistic VCS setup for running covimport utility
setenv VCS_HOME /p/hdk/rtl/cad/x86-64_linux26/synopsys/vcsmx/T-2022.06-SP2
setenv SNPSLMD_LICENSE_FILE 26586@synopsys13p.elic.intel.com:26586@synopsys10p.elic.intel.com
 
# minimalistic ucis2ucd setup    
setenv CAD_ROOT /p/hdk/rtl/cad/x86-64_linux26/dt/
setenv PATH $CAD_ROOT/coverage_converter/22.3.2_stOpt64/bin/:$PATH
setenv CDS_LIC_FILE 5280@cadence16p.elic.intel.com:5280@cadence17p.elic.intel.com
setenv LD_LIBRARY_PATH /p/hdk/rtl/cad/x86-64_linux26/synopsys/vcsmx/S-2021.09-SP2-2/suse64/lib:/p/hdk/rtl/cad/x86-64_linux30/cadence/xcelium/22.01.001/tools/lib/64bit

```
***Imprtant Note***:
- This setup is minimalistic and enables generating VDB/UNICOV data from UTDB.  It is not enough for coverage analysis in Verdi or vManager. 

---
# 10. Global Configuration
Global Configuration enables several settings to globally control all or parts of the APIs behavior.

It is arranged in several categories and several settings in each category.

The interface for the setting includes a python script utdb global object, or a dedicated environment variable.

## 10.1 Configuration Categories and settings
These are some useful (full list can be found in UTDB reference manual as well as calling **config.help()** method):

| Category | setting | Description |
| -------- | ------- | ----------- |
| logging | console_log_level | The log level for messages going to the console/stdout |
| logging | logfile_log_level | The log level for messages going to the log file |
| logging | logfile_path | The log file path. Hostname and PID may optionally get appended to it based on the append_host_pid_to_logfile_path setting |
| logging | append_host_pid_to_logfile_path | If true, the current host name and process id are added to the name of the log file as means for uniqueness |

## 10.2 Configuration control methods
There are multiple methods to control the values of Global Configurations settings:

* Python script - uses global utdb config object to set values for the different settings.
* User app command line options using the config set_from_cmd_line method.
* Environment variable - set environment variable UTDB_CONFIG similar to command line options.

``` py

# using config global object
config.logging.logfile_log_level=10
config.logging.console_log_level=2
 
# using user command-line arguments
call:
user_app.py --utdb.logging.logfile_log_level=10 --utdb.logging.console_log_level=2
script:
cmd_line_str = # convert command line parameters to string
config.set_from_cmd_line(cmd_line_str)
 
# using environment variable setting as command line string
setenv UTDB_CONFIG "--utdb.logging.logfile_log_level=10 --utdb.logging.console_log_level=2"

```

# 11. Utilities

## 11.1 Uploader Template Generator
Uploader template Generator (UTG) is a command line utility tool to help create basic uploader python script templates based on tabular logs.

As part of template generation, UTG will auto detect what are the relevant fields and record types to add to the generated table schema object.

### 11.1.1 Getting started
UTG executable path is **UTDB_HOME/bin/uploader_template_generator**

A simple run command to generate template:

`UTDB_HOME/bin/uploader_template_generator -i path/to/log`

### 11.1.2 Command line options

| Option | Details |
| ------ | ------- |
| -h [--help] | Produce help message |
| -i [--input_file] | (mandatory) Path (absolute or relative) to input log file. Uploader template and schema generated will be based on input file. |
| -o [--output_path] | Path to store generated template. If not set default location will be current working directory. |
| --separator | Set separator to set as Reader separator in generated template. Default value is “|". |
| --include | Set include regex to set as Reader include regex in generated schema. Default is “.*” (include all lines). |
| --type_selector | Index of field to be used as selector when using a log with multi-schema (several number of record types). Default is 0. |

### 11.1.3 Usage example

`$UTDB_HOME/bin/uploader_template_generator -i path/to/tabular_log.log -o ./test.out --include="^[0-9].*"`


On screen UTG output information:
```
input file is: path/to/tabular_log.log
output file is: <path to current directory>/test.out
uploader generation finished successfully.
python script location: <path to current directory>/test.out
operation took 26.6441ms

```

Generated template (multi schema example)

``` py
#!/usr/intel/pkgs/python3/3.6.3a/bin/python3.6
 
import os
 
utdb_home_key = "UTDB_HOME"
utdb_home = os.getenv(utdb_home_key)
 
if utdb_home is None or not os.path.isdir(utdb_home):
        raise RuntimeError(utdb_home_key + " is not properly defined!")
 
utdb_libs = os.path.join(utdb_home, "lib")
os.sys.path.insert(0, utdb_libs)
 
# Bringing the required dependencies:
from uploader import *
 
schema = table_schema()
schema.add_record_schema('N', [
        field(name='TIME', type=<set_type>),
        field(name='TYPE', type=<set_type>),
        field(name='DATA1', type=<set_type>),
        field(name='DATA2', type=<set_type>)])
schema.add_record_schema('R', [
        field(name='TIME', type=<set_type>),
        field(name='TYPE', type=<set_type>),
        field(name='DATA1', type=<set_type>)])
 
reader = Reader(file_path="/ path/to/tabular_log.log",schema=schema,separator='|', type_selector=FieldSelector(selector_field=0))
 
writer = Writer("<utdb connection string placeholder>")
writer.write(reader)
writer.close()

```

***Notes:***
- UTG currently supports only tabular logs that contain #header lines to detect the log schema and record types (e.g #header,R,Time,type,data1 lines).
- The UTG generates a template. This means that the outputted script (template) will need additional information in the relevant place holders such as field types and writer connection string to work properly.

## 11.2 UTDB Shell App
UTDB shell app is a command line tool designed to supply an efficient and easy way to get data on a UTDB.

### 11.2.1 Getting started
The shell app may be used in two modes: batch and interactive. The general usage of the app looks like:

`$UTDB_HOME/bin/utdb [OPTIONS] COMMAND [ARGS]`

where *COMMAND* and its optional ARGS is one of those described below. Use --help for details.

```
> $UTDB_HOME/bin/utdb --help
 
Usage: utdb [OPTIONS] COMMAND [ARGS]...
 
Options:
  -h, --help                      Show this message and exit.
  -v, --verbosity VERBOSITY       verbosity level  [1<=x<=10]
  -l, --logfile FILENAME          log file name
  -V, --logfile_verbosity VERBOSITY
                                  log file verbosity level  [1<=x<=10]
 
Commands:
  describe  Shows information about a utdb
  dump      Prints out the contents of a utdb
  grep      Searches a utdb for specific values by regular expression
  man       Opens UTDB API User Guide in firefox
  query     Execute a query and prints out the results
  quit      Exits interactive mode
  run       Runs a command with env vars pointing to this UTDB version
  view      Opens UTDB Viewer GUI

```

When invoked with a COMMAND, the app will execute the command and exit. When invoked without a COMMAND, the app will enter an interactive mode:

`> $UTDB_HOME/bin/utdb`

In the interactive mode, the above will open a prompt in which any of the available commands may be typed.

To get help on individual command use:

`$UTDB_HOME/bin/utdb COMMAND --help`

### 11.2.2 Available commands
- **describe**: shows information about a UTDB
- **dump**: prints out the contents of a UTDB
- **grep**: searches a UTDB for specific values
- **man**: Opens UTDB API User Guide in firefox
- **query**: executes a query on a UTDB
- **run**: Runs a command with env vars pointing to this UTDB version
- **view**: opens UTDB viewer for a given UTDB

### 11.2.3 Usage example
```
$UTDB_HOME/bin/utdb
> describe /nfs/site/…/utdb
# prints out the schema of the UTDB: the record-types, the fields and their datatype #
 
> dump -l 20 -d /nfs/site/…/utdb
> dump -l 20 -d /nfs/site/…/utdb -o first_20_records.txt
# prints out the first 20 records of the UTDB in PSV (default) format
 
> query 'where(match(trace.cpurequest.ADDRESS, "0x3*0B0*", kind="wildcard", ignore_case=False))' trace=/nfs/site/…/utdb
# prints out the result of the query in PSV format #

```

## 11.3 pm_to_uploader utility
***pm_to_uploader** is a perl script that helps converting legacy uploading 2logdb pm files to new uplader API uploading files

pm_to_uploader.pl is located at $UTDB_HOME/bin/pm_to_uploader.pl

use --help to get help on usage and parameters

```

$UTDB_HOME/bin/pm_to_uploader_new.pl --help

DESCRIPTION
    Shell tool for the convertion of pm configurations to new Uploader API.

    usage : pm_to_uploader.pl --pm-file <pm-file> [options]

    usage example :
    $UTDB_HOME/bin/pm_to_uploader.pl -pf $WORKDIR/pm_files/tracker.pm -o
    $OUTDIR/upload_tracker.py

    $UTDB_HOME/bin/pm_to_uploader.pl -pf $WORKDIR/pm_files/tracker.pm -o
    $OUTDIR/upload_tracker.py --no-file-match

OPTIONS
    -pf, --pm-file
        The existing legacy pm file that needs to be converted to uploader
        APIs.

    -o, --output-path
        The path to the generated script location. Default :
        <run_dir>/<pm_file name with '.py' suffix>.

    -f, --framework
        Create uploader script that uses uploader framework class and in example:
        "$UTDB_HOME/examples/uploader_base_class_examples/idi_tracker_uploader.py".

    -nm, --no-file-match
        Create uploader script without file name pattern matching (only for
        single config pm files)

    -h, --help
        Print this help screen. Press q to exit.

```



# 12. UTDB API Examples
Running examples can also be found under UTDB release home directory ($UTDB_HOME/examples).
UTDB examples includes working code examples that can be used as copy/modify code:

- Uploading data from different file formats and manually creating UTDB for checker testing.
- Using different query constructs.
- Setting events and detecting flows in UTDB trace.
- Defining and collecting coverage from UTDB database.

In addition, the examples include instructed labs for the different UTDB APIs capabilities (uploading, query, flow detection, coverage collection).

This section contains few UTDB code examples and explanations.

## 12.1 Checker Query example

This example demonstrates:

- Connecting to the UTDB database
- Building a query for cpurequest or nbresponse record types
- Printing each record in the results and checking that for each request we get a response

The example code assumes environment setting for UTDB_HOME environment variable.

``` py

#!/usr/intel/pkgs/python3/3.6.3a/bin/python3.6 
import os
 
local = os.path.dirname(os.path.realpath(__file__))
 
utdb_home_key = "UTDB_HOME"
utdb_home = os.getenv(utdb_home_key)
 
if utdb_home is None or not os.path.isdir(utdb_home):
    raise RuntimeError(utdb_home_key + " is not properly defined!")
 
utdb_libs = os.path.join(utdb_home, "lib")
 
os.sys.path.insert(0, utdb_libs)
 
# Bringing all UTDB API
from UTDB import *
 
# Connecting to the 'request_response' trace:
trace = connect(os.path.join(local, 'request_response'))
 
# Define origin
q = from_(trace)
# Filter out irrelevant data
q = q.where(record_type(trace.cpurequest) | record_type(trace.nbresponse))
# Define order
q = q.sort_by((trace.all.TIME, ASC))
# Get subset of fields
q = q.fields(trace.all.RECORD_TYPE, trace.all.TIME, trace.all.COREREQID)
 
# Execute query:
res = fetch(q)
 
req_ids = set()
 
# Check if every request has a response with same id:
for r in res:
    print(r)
    id = r.COREREQID
    if r.RECORD_TYPE == "CPURequest":
        if id in req_ids:
            raise RuntimeError(str(id) + " used in previous request!")
        req_ids.add(id)
    elif r.RECORD_TYPE == "NBResponse":
        if id not in req_ids:
            raise RuntimeError(str(id) + " hasn't been seen in a request!")
        req_ids.remove(id)
 
if len(req_ids) > 0:
    raise RuntimeError("Not all requests got their response!")
 
print("The check has successfully passed!")

```

## 12.2 Uploading example

This example demonstrates:

- Defining a schema with fields configuration
- Reading data in batches
- Writing data in batches

The example code assumes environment setting for UTDB_HOME environment variable. 

``` py
#!/usr/intel/pkgs/python3/3.6.3a/bin/python3.6
import os
 
utdb_home_key = "UTDB_HOME"
utdb_home = os.getenv(utdb_home_key)
 
if utdb_home is None or not os.path.isdir(utdb_home):
    raise RuntimeError(utdb_home_key + " is not properly defined!")
 
utdb_libs = os.path.join(utdb_home, "lib")
 
os.sys.path.insert(0, utdb_libs)
 
# Bringing all UTDB API
from UTDB import *
 
# create Table Schema setting fields configuration via constructor
schema = table_schema()
schema.add_record_schema([
    field(name='TIME', type=FieldType.INT),
    field(name='TYPE', type=FieldType.STRING, lookup=True),
    field(name='DATA', type=FieldType.STRING, output=False),
    field(name='INFO', type=FieldType.STRING, input=False),
])
 
# define Reader
reader = Reader(file_path='demo_idi.log', schema=schema, separator="\|", include= '^[0-9].*')
 
# define Writer
writer = Writer('demo_idi_utdb') 
try:
    # iterate over batches, uses default batch size
    for table in reader.read(batch_size=10):
        # iterate over each line in table and process it
        for line_number in range(table.size):
            record = table[line_number]
            # set 'INFO' output field value
            record['INFO'] = record['TYPE'] + '_' + record['DATA']
 
        # write the processed table
        writer.write(table)
 
except UploaderException as e:
    error_table = e.get_error_table()
    for err_i e.errors. number_of_errors:
        print(error_table[err_i]['LINE_NUMBER'],
            error_table[err_i]['ERROR_NAME'],
            error_table[err_i]['ERROR_MSG']
        )

```
