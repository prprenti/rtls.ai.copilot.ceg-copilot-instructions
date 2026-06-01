---
applyTo: "src/val/griffin**,src/val/utdb,**/*griffin*.prompt.md"
---

[TOC levels=1,2]

# 1 UTDB Uploader
This section describes Uploader API methods and objects:
 
## 1.1 RecordSchema object
RecordSchema contains the fields and their configuration of records in UTDB. It can contain associated record type name or can be nameless (in case of single record type table. RecordSchema is created by calling TableSchema **add_record_schema()** method.

***RecordSchema related methods and attributes:***

- **add()** - method to add a new Field to the schema
- **contains()** - method to check if a certain Field name exists
- **get_field_index()** - method to get field index by name
- **size** - attribute that returns the number of fields in the schema


### 1.1.1 add method
RecordSchema **add()** methods adds (append to the end) a single new Field object to the fields list.

***Syntax:***
<record_schema>.add(<field>)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| field | Field object | A Field object to add to the record schema fields list. |

***Notes:***

- The Fields names within the RecordSchema fields list must be unique.
- The order of the input fields usually matches the order of the data fields in the file.
- RecordSchema can not hold more then one field with MULTI_CELL type.

***Code Example:***
``` py

# create a new empty TableSchema object
schema = table_schema()
rec_schema = schema.add_record_schema()
 
# add a new Field using addition API
rec_schema.add(field(...))

```

### 1.1.2 contains method

RecordSchema **contains()** methods accepts field name as parameter and returns True if it exists and False otherwise.

***Syntax:***

<col_exists>  = <schema>.contains (<field_name>)

***Returns:*** True if field name exists. False otherwise.

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| field_name| String | The field name to look for in the field list |

***Code Example:***
``` py

# create TableSchema with field
col = [field(name='my_field', type=FieldType.BOOL)]
schema = table_schema()
record_schema = schema.add_record_schema(col)
 
# get True if field exists in schema
field_exists = record_schema.contains('my_field')

```

### 1.1.3 get_field_index method
RecordSchema **get_field_index()** method accepts field name as a parameter and returns the index of the field in the field list.

***Syntax:***

<field_index> = <record_schema>. get_field_index (<field_name>)

***Returns:*** The index of the field or -1 if field does not exist

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| field_name | String | The field name in the field list to get the index for |


***Code Example:***
``` py

# create TableSchema with field
col = field(name='my_field', type=FieldType.BOOL)
schema = table_schema()
record_schema = schema.add_record_schema()
record_schema.add(col)
 
# get field index
field_index = record_schema.get_field_index('my_field')

```

### 1.1.4 fields method
RecordSchema **fields()** method returns a list of the fields in the RecordSchema.

***Syntax:***

<list_of_fields> = <record_schema>.fields()

***Returns:*** list of fields

***Code Example:***
``` py

# create TableSchema with field
col = field(name='test_col', type=FieldType.BOOL)
schema = table_schema()
record_schema = schema.add_record_schema()
record_schema.add(col)
 
fields = record_schema.fields()

```

### 1.1.5 size attribute
RecordSchema **size** attribute returns the number of fields in the schema.

***Syntax:***

<number_of_fields> = <record_schema>.size

***Returns:*** Number of fields in the schema.

***Code Example:***
``` py

# create TableSchema with field
col = field(name='test_col', type=FieldType.BOOL)
schema = table_schema()
record_schema = schema.add_record_schema()
record_schema.add(col)
 
number_of_fields = record_schema.size

```
## 1.2 TableSchema object
TableSchema contains the configuration of the data that needs to be read and stored in UTDB. It contains one or more RecordSchemas that differ by name, or one nameless RecordSchema.

***TableSchema related methods and attributes:***

- **table_schema()** - global constructor method
- **add_record_schema()** - method to add a new named/nameless record schema to the table schema
- **get_record_schema()** - method to get named/nameless record schema to the table schema
- **contains()** - method to check if a certain RecordSchema name exists.
- **record_schemas()** - method returns a list of the contained records schemas

### 1.2.1 table_schema function
**table_schema()** is a global function to create a new, empty TableSchema.

***Syntax:***

Create empty TableSchema
<table_schema> = table_schema(hierarchical = <is_hierarchical>, record_type_name_case=<name case>, field_name_case=<name case>)

Create TableSchema with single nameless RecordSchema
<table_schema> = table_schema(<field list>, hierarchical = <is_hierarchical>, record_type_name_case=<name case>, field_name_case=<name case>)

***Returns:*** TableSchema object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| fields_list | List of Fields | List of Field configurations to add to the TableSchema |
| **hierarchical** | Boolean | Should this schema refer to hierarchical data, adding hierarchical structure functionality to each record. **Default:** False |
| **record_type_name_case** | NameCase enum | Record type name case to be enforced. **Default:** NameCase.ANY |
| **field_name_case** | NameCase enum | Field name case to be enforced. **Default:** NameCase.UPPER |


***Notes:***
- see [NameCase enum definition](#165-namecase-enum) for more details 
- Calling **table_schema()** with a field list will add a RecordSchema without a name (nameless).
- There can only be one nameless RecordSchema in the TableSchema.

***Code Example:***
``` py

# create table schema (using default flat structure)
schema = table_schema()
 
# create explicit flat table schema
schema = table_schema(hierarchical=False)
  
# create hierarchical table schema
schema = table_schema(hierarchical=True)

```

### 1.2.2 add_record_schema method

TableSchema **add_record_schema()** method accepts name and field list parameters and adds a new RecordSchema accordingly.

***Syntax:***

Add nameless RecordSchema  
<record_schema> = <schema>.add_record_schema([<fields_list>])

Add named RecordSchema  
<record_schema> = <schema>.add_record_schema(<record_type_name> [, <fields_list>] [, <extends>])

***Returns:*** RecordSchema object

***Parameters:***

| Parameter Name   | Type           | Description                                               |
| ---------------- | -------------- | --------------------------------------------------------- |
| record_type_name | String         | The record schema name to use as an identifier (optional) |
| fields_list      | List of Fields | List of Field configurations to add to the TableSchema    |
| extends          | RecordSchema   | Another record schema that is going to be extended        |

***Notes:***

- Calling **add_record_schema()** without a name will add a nameless record schema. There can only be one nameless schema in the TableSchema.
- Adding a named schema after adding a nameless schema will throw UploaderException.
- Adding nameless schema after adding named a schema will throw UploaderException.
- Only named schemas can be extended.
- Fields of extending schema will contain all fields from base appended by fields provided in **add_record_schema()**.

***Code Example:***

``` py
# Create empty table schema
schema = table_schema()

# Add nameless empty RecordSchema. Will fail if schema has another RecordSchema
empty_rec_schema = schema.add_record_schema()

# Add named empty RecordSchema. Will fail if schema has nameless RecordSchema
empty_named_rec_schema = schema.add_record_schema('my_record_type')

# Define list of fields
fields = [
    field(name='DATA0', type=FieldType.STRING),
    field(name='HIGH_PERFORMANCE', type=FieldType.STRING)
]

# Add named RecordSchema with list of Fields. Will fail if schema has nameless RecordSchema
named_record_schema = schema.add_record_schema('my_record_type', fields)

# Add nameless RecordSchema with list of Fields. Will fail if schema has other RecordSchema
nameless_record_schema = schema.add_record_schema(fields)

extension_fields = [field(name="EXTENDED_DATA")]

# Add extended RecordSchema. Will have fields: DATA0, HIGH_PERFORMANCE, EXTENDED_DATA
extended_record_schema = schema.add_record_schema('extended_record_type', extension_fields, extends=named_record_schema)

```

### 1.2.3 get_record_schema method

The TableSchema **get_record_schema()** method returns a reference to a specified record schema. 

***Syntax:***

<record_schema> = <schema>.get_record_schema()

<record_schema> = <schema>.get_record_schema(<record_type_name>)

***Returns:*** RecordSchema object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| record_type_name | String | The record schema name to look for in the TableSchema. |

 ***Notes:***
- Calling get_record_schema without a name will return the nameless record schema that the table schema contains, given that it has one. Otherwise, it will throw UploaderException.
- If a named RecordSchema was not found, it will throw UploaderException.

***Code Example:***
``` py

# create table schema
schema = table_schema()
# add named empty RecordSchema
empty_named_rec_schema = schema.add_record_schema("my_record_type")
 
<record schema> = schema.get_record_schema("my_record_type")

```

### 1.2.4 contains method
TableSchema **contains()** methods accepts RecordSchema name as parameter and returns True if it exists and False otherwise.

***Syntax:***

<record schema> = <schema>.get_record_schema(<record_type_name>)

***Returns:*** True if RecordSchema name exists. False otherwise

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| record_type_name | String | The record schema name to look for in the TableSchema. |

***Notes:***

***Code Example:***
``` py

# create TableSchema with field
fields = [field(name='my_field', type=FieldType.BOOL)]
schema = table_schema()
schema.add_record_schema("my_rec_type_name", fields)
 
# get True if RecordSchema exists in schema
schema_exists = schema.contains("my_rec_type_name")

```

### 1.2.5 record_schemas method
TableSchema record_schemas method returns a list of all RecordSchemas in TableSchema.

***Syntax:***

<record_schema_list> = <schema>.record_schemas()

***Returns:*** list of RecordSchemas

***Code Example:***
``` py

# create TableSchema with field
fields1 = [field(name='field_name_1', type=FieldType.BOOL)]
fields2 = [field(name='field_name_2', type=FieldType.BOOL)]

schema = table_schema()

schema.add_record_schema("rec_type_1",fields1)
schema.add_record_schema("rec_type_2",fields2)
  
# returns a list with RecordSchema objects for rec_type_1 and rec_type_2
record_schema_list = schema.record_schemas()
 
```

## 1.3 FieldSelector object
FieldSelector contains the mapping of raw rows to a record schema using a specified field.

FieldSelector related methods:

- **FieldSelector()** - constructor method

### 1.3.1 FieldSelector constructor
FieldSelector is created using the **FieldSelector()** constructor method

***Syntax:***

<selector> = fieldSelector(selector_field=<field_index>, mapping=<mapping>)

***Returns:*** New fieldSelector object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **selector_field** | Number | Index of the field to use as a selector |
| **mapping**        | Dictionary | Contains the mapping of a given field content to the record_schema name |

***Notes:***

***Code Example:***
``` py

# define new FieldSelector
field_selector = FieldSelector(selector_field = 1, mapping={"R":"RETIREMENT","N":"NUKE"})

```

## 1.4 CustomSelector object
CustomSelector contains the mapping of raw rows to a record schema using a user defined function.

CustomSelector related methods:
- **CustomSelector()** - constructor method


### 1.4.1 CustomSelector constructor
CustomSelector is created using **CustomSelector()** constructor.

***Syntax:***

<selector> = CustomSelector(type_lambda=<user_defined_function>)

***Returns:*** New CustomSelector object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **type_lambda** | Function | User defined function to determine a row’s record schema name |


***Notes:***
- lambda Function input: list of cells split row
- lambda Function Output: schema name (String)

***Code Example:***
``` py

# define new CustomSelector
custom_selector= CustomSelector(
    type_lambda=(lambda cells: "RETIREMENT" if cells[1] == "R" else "NUKE")))

```

## 1.5 Field object
Field contains the configuration of a field in the data. A Field is constructed using its constructor method, which takes the configuration values as parameters.

***Field related methods and attributes:***

- **field()** - global constructor function
- **name** - attribute of field name
- **type** - attribute of field data type
- **base** - input numeric string base for numeric fields (decimal, hexadecimal or binary) 
- **format** -  textual representation format string
- **mode** - field can be set as read, write or both
- **null_value** - string representing null value in the input text
- **convert** - method pointer or lambda function that will manually convert the input string to the relevant field value
- **width** - for width based input line splitting
- **input_position** - the index of the input column to assign for the field
- **display_name** - name to use as header name when using **dump()** API 
- common time converters (cleans extra characters and convert to a number with potentially different scale
    - **ps_str_to_ps** - convert picosecond text value to numeric value
    - **ns_str_to_ps** - convert nanosecond text value to picosecond numeric value (multiple by 1000)
    - **us_str_to_ps** - convert microsecond text value to picosecond numeric value (multiple by 1000000)

***Note:*** some attributes (e.g. base, format) may have different values for each record type

### 1.5.1 Field constructor
The Field object is created using **field()** global constructor function.
Field can be create as new field or as a copy of other field where all field properties of the newly created object are initialized by copying the contexts of an existing object except the properties given as named arguments to filed function.

***Syntax:***

<field> = field(name=<NAME> [,type=<data_type>] [, base=[DEC|BIN|HEX]] [, format=<string>] [, mode=[READ|WRITE|READ_WRITE]] [, null_value=<regex>] [, convert=<method>] [, is_lookup=[True|False]] [, index=[True|False]] [,width=<number>] [, input_position=<number>] [, display_name=<string>])

<field> = field(<field>, name=<NAME> [,type=<data_type>] [, base=[DEC|BIN|HEX]] [, format=<string>] [, mode=[READ|WRITE|READ_WRITE]] [, null_value=<regex>] [, convert=<method>] [, is_lookup=[True|False]] [, index=[True|False]] [,width=<number>] [, input_position=<number>] [, display_name=<string>])

***Returns:*** Field object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **name** | String | The name of the field in the data output. Must apply python variable name constraints. (Mandatory)|
| **type** | FieldType enum | Enum value that indicates the output filed data type (see [FieldType enum definition](#161-fieldtype-enum)). ***default:*** **FieldType.STRING** |
| **base** | Base enum | Enum value that indicates the base of the textual value representation. The base will direct the reader how to cast a input numeric string from a file to a number (see [Base enum definition](#162-base-enum)). ***Default:*** **Base.DEC** |
| **format** | String | A string that represents the python value formatting (e.g. '0x{:x}'. |
| **mode** | RWMode enum | (see [Base enum definition](#163-rwmode-enum)). ***Default:*** **RWMode.READ_WRITE** |
| **null_value** | Regex string | A string regex. If the field string value will match the regex the reader will set the read value to Null. |
| **convert** | Method/Lambda | A method or lambda function that will revive the read input string and return the expected output value for that field. (see [Base enum definition](#164-time-conversion-functions))|
| **lookup** | Boolean | For performance improvement (Depends on UTDB implementation). **True** will create a lookup table for the field's values. **False** will not create a lookup table for the fields values. ***Default:*** **False** |
| **index** | Boolean | For performance improvement (Depends on UTDB implementation). **True** will create database index the field. **False** will not create database index the field. ***Default:*** **False** |
| **width** | Number | Defines the number of characters (size) of a field in the input log. Used by the fixed width reader to process lines. |
| **input_position** | Number | Defines the index of a column in the input log (after splitting). Used to map a field output position to the position in the input file, rather than the position that was defined in the schema. |
| **display_name** | String | Defines the name to use as header name when suing dump. If not defined, dump will use field name as display name |

***Notes:***
- All numeric values are 64 bits or arbitrary size integers
- **convert** method must return the configured data type for that field.
- **input_position** is between 0 and number of columns (zero based).
- Defining a field without **input_position** after a field with **input_position** will throw an exception.
- Using **input_position** and width will throw an exception.
- Using **input_position** and **FieldType.MULTI_CELL** will throw an exception. 
- Using **input_position** and **RWMode.WRITE** mode will throw an exception.
- Octal **format** is not supported 

***Code Example:***
``` py

# simple int field
field(name='TIME', type=FieldType.INT)

# string field with optimized length and request for a lookup table
field(name='TYPE', type=FieldType.STRING, lookup=True)

# read it, but don't save to the DB
field(name='DATA', type=FieldType.STRING, mode=RWMode.READ),

# prepare an empty field for me to populate
field(name='DATA0', type=FieldType.STRING, mode=RWMode.WRITE)

# request the database to create field index for optimization
field(name='HIGH_PERFORMANCE_SEARCH_FIELD', type=FieldType.STRING, index=True)

# will fail if the convert function return value is not int
field(name='USER_CONVERTER_FIELD', type=FieldType.UINT, convert=remove_hex_prefix, format='0x{:x}')

# will fail if the return value is not int (e.g. convert float to int)
field(name='USER_LAMBDA_CONVERTER_FIELD', type=FieldType.UINT, convert = lambda val: int(val.split('.')[0]))

# set automatic null value detection
field(name='EXPLICIT_NULL_VALUE_FIELD', type=FieldType.STRING, null_value='--')

# set TIME data to be from the second column (zero based)
f1 = field(name='TIME', type=FieldType.INT, input_position = 2)

# create field as copy from predefined field and override the format attribute value
f2 = field(f1, format='0x{:x}')

```

### 1.5.2 name attribute
Field **name** attribute returns the name of the field. This is a read only attribute.

***Syntax:***

<field_name> = <field>.name

***Returns:*** Field name string

***Notes:***

***Code Example:***
``` py

# create Field object
fld = Field(name='TEST', type=FieldType.BOOL)
 
# get Field name (= 'TEST')
col_name = fld.name

```

### 1.5.3 type attribute
Field type attribute can be used to get or set the field data type.

***Syntax:***

<field_type> = <field>.type

<field>.type = <field_type>

***Returns:*** FieldType enum (see [FieldType enum definition](#161-fieldtype-enum))

***Notes:***

***Code Example:***
``` py

# create Field object
fld = Field(name='TEST', type=FieldType.BOOL)
 
# get Field type (= FieldType.BOOL)
col_type = fld.type

```

## 1.6 field attributes Enum values and functions

### 1.6.1 FieldType enum
FieldType enum lists the valid field types in the system.

***Enum Values:***

| Enum Value | Description | 
| -------------- | ---- |
| FieldType.BOOL | Boolean value (True, False) |
| FieldType.INT | 64bits signed integer |
| FieldType.STRING | String |
| FieldType.UINT | 64bits unsigned integer |
| FieldType.AINT | Arbitrary sized integer |
| FieldType.DOUBLE | Floating point number |
| FieldType.MULTI_CELL | holds multiple cells in raw form (string). Will use greedy data collection, i.e. will collect as much cells as possible while fulfilling all other fields requirements |


### 1.6.2 Base enum

***Enum Values:***

| Enum Value | Description | 
| -------------- | ---- |
| Base.HEX | Hexadecimal textual format value |
| Base.DEC | Decimal textual format value |
| Base.BIN | Binary textual format value |


### 1.6.3 RWMode enum

***Enum Values:***

| Enum Value | Description | 
| -------------- | ---- |
| RWMode.READ | Will read data from input file, will not write the data to the output. |
| RWMode.WRITE | Will not read data from input file,  will write the data to the output. |
| RWMode.READ_WRITE | Will read from input file and write data to the output. |

### 1.6.4 Time conversion functions

- **ps_str_to_ps** - convert picosecond text value to numeric value
- **ns_str_to_ps** - convert nanosecond text value to picosecond numeric value (multiple by 1000)
- **us_str_to_ps** - convert microsecond text value to picosecond numeric value (multiple by 1000000)

### 1.6.5 NameCase enum
**NameCase** enum relates to record typ names and field names. These names case sensitivity can be forced by the uploader or modified when connecting to existing UTDB storage based on the ability to convert and eliminate duplications when the case is changed.

***Enum Values:***

| Enum Value | Description | 
| -------------- | ---- |
| NameCase.LOWER | Force user lower case when uploading and convert to lower case when connecting to trace. |
| NameCase.UPPER | Force user UPPER case when uploading and convert to UPPER case when connecting to trace. |
| NameCase.ANY   | Will enforce to convert the names case. |


### 1.6.6 SplitMode enum

***Enum Values:***

| Enum Value | Description | 
| -------------- | ---- |
| **SplitMode.separator** | Using separator token (or regex) to split input line into fields values. |
| **SplitMode.fixed_width** | Using fixed set of widths provided in the fields configuration. |


### 1.6.7 UTDB storage types
UTDB supports multiple storage and database engine types. Storage type are specified as strings.

***supported storage types:***

| Storage Type | Description |
| ------------ | ----------- |
| "logdb" (default) | This storage type is based on local sql engine and storage. It is the legacy storage and planed to be replaced with the other storage types during 2024 |
| "pg" | This storage type uses postgresql database engine and storage
| "pgpqt" | This storage type uses postgresql database engine and parquet storage files


## 1.7 DataTable
The DataTable contains the data read by the reader or created by the user. It contains the data schema and a list of the records with their field’s values. The records can be accessed by index. DataTable can be constructed programmatically by the user using DataTable construction methods.

***DataTable related methods and attributes:***

- **DataTable()** - constructor method
- **add_record()** - method to add a new record to the DataTable records list
- **remove_record()** - method to remove a record from DataTable records list
- **is_hierarchical()** - method to check whether the DataTable is hierarchical
- **records** - attribute that returns a list of records
- **size** - attribute that returns the number of records

### 1.7.1 DataTable constructor
DataTable is created using **DataTable()** constructor or by calling the Reader read method.

***Syntax:***

<table> = DataTable(<table_schema>)

***Returns:*** New DataTable object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| table_schema | TableSchema | TableSchema object containing fields' information and configurations of the table. Cannot be changed after constructor. |

***Notes:***

***Code Example:***
``` py

# create schema
schema = table_schema(hierarchical=True)
 
# define list of fields
fields = [
    field(name='DATA0', type=FieldType.STRING),  
    field(name='HIGH_PERFORMANCE', type=FieldType.STRING)
    ]
# add named RecordSchema with list of Fields
schema.add_record_schema('my_record_type', fields)
 
# create a new DataTable based on hierarchical schema
table = DataTable(schema)

```

### 1.7.2 add_record method
DataTable **add_record()** method is used to add a new data record to the DataTable. It accepts the record type name and index (optional) as parameters and returns a new record object that can be used to set the record type fields values (see Record object section for more info).

***Syntax:***

<record> = <table> add_record(<record_type_name>)

<record> = <table> add_record()

<record> = <table> add_record(<index>, <record_type_name>)

<record> = <table> add_record(<index>)

***Returns:*** Record object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| index | Number | Index to insert a new record. |
| record_type_name | String | Name of the new record's type |

***Notes:***

- Throws UploaderException if index is negative or greater than the size of the table.
- If no record_schema_name is provided, will try to use the nameless recordSchema. If it doesn’t exist, will throw UploaderException.
- If an index is used, all the indexes above it will increase.

***Code Example:***
``` py 

# add a new record of type 'my_record_type'
record = table.add_record('my_record_type')
record = table.add_record(2,'my_record_type')

```

### 1.7.3 remove_record method
DataTable **remove_record()** method is used to remove existing records from the DataTable. It accepts an index as parameter.

***Syntax:***

<table>.remove_record(<index>)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| index | Number | Index of the record to remove. |

***Notes:***

- Throws UploaderException if index is negative or greater than the size of the table.
- Indexes above the selected one are decreasing.

### 1.7.4 is_hierarchical method
DataTable **is_hierarchical()** is used to check whether the DataTable is hierarchical.

***Syntax:***

<table>.is_hierarchical()

***Returns:*** Boolean

***Parameters:*** None

***Code Example:***
``` py

schema = table_schema(...)
 
# create data table
table = DataTable(schema, hierarchical=True)
table.is_hierarchical() # True

```

### 1.7.5 size attribute
DataTable **size** attribute returns the number of the records in the table.

***Syntax:***

<num_records> = <table>.size

***Returns:*** number of records in the table

***Notes:***

***Code Example:***
``` py

schema = table_schema(...)

# create data table
table = DataTable(schema)
  
# add a new record of type 'my_record_type'
record = table.add_record('my_record_type')
 
num_records = table.size

```

## 1.8 Record object
Uploader Record object represents a set of fields' values. The fields can be assessed as dictionary using field name as a key. In the record, fields’ values can be read or written based on the field’s configured type.

***Record related methods and attributes:***

- **record_schema()** - method to get the record schema object
- **size** - attribute to get the number of fields in the record
- **[]** - operator accessor to record fields' values
- **add_record()** - used with a hierarchical DataTable to add children to a record

### 1.8.1 record_schema method
**record_schema()** method returns the RecordSchema object related to the record fields.

***Syntax:***

<schema> = <record>.record_schema()

***Returns:*** RecordSchema object

***Notes:***

***Code Example:***
``` py

schema = table_schema(...)

# create data table
table = DataTable(schema)
 
# add new record of type 'my_record_type'
record = table.add_record('my_record_type')
 
rec_schema = record.record_schema()
print(rec_schema.name)  #prints 'my_record_type'
for f in rec_schema.fields():
    # f is Field object

```

### 1.8.2 size attribute
Record **size** attribute returns the number of fields in the record.

***Syntax:***

<num_fields> = <record>.size

***Returns:*** number of fields

***Notes:***

***Code Example:***
``` py

schema = table_schema(...)
 
# create data table
table = DataTable()
 
# add record type and schema
table.add_record_type('my_record_type', schema)
 
# add new record of type 'my_record_type'
record = table.add_record('my_record_type')
 
num_fields = record.size

```

1.8.3 [] operator
Record **[]** operator is used to set or get the field value in the record based on the field name or the field index - based on the record type.

***Syntax:***

<value> = <record>.[<field_name> | <field_index>]

***Returns:*** field value

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| field_name | String | The name of a field based on the schema fields configuration. |
| field_index | Number | The index of the field in the record based on the schema fields order. |

***Notes:***

***Code Example:***
``` py

# iterate through DataTable records
for rec in table
    # set field 'C' to be field index 1 + field index 2
    rec['C'] = rec[1] + rec[2]
 
    # set field B' to be field 'C' as string + ' ns'
    rec['B'] = str(rec['C'] + ' ns'

```

### 1.8.4 add_record
**add_record()** method is used to add child records to the current record, returning the new record to be accessed. The child records are added as the last children for each direct parent record.

***Syntax:***

<record> = <record> add_record(<record_type_name>)

<record> = <record> add_record()

***Returns:*** Record object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| record_type_name | String | Name of the record's type to create a new record |

***Notes:***

- Can be used only when the schema has hierarchical = True

***Code Example:***
``` py

schema = table_schema(hierarchical=True)
table = DataTable(schema)
 
# add root record
record = table.add_record()
 
# add child record for hierarchical DataTable
child = record.add_record()
 
# access child record
child["TIME"] = ...

```

## 1.9 Reader object
The Reader object is used to read test output file data into the uploader.

***Reader related methods and attributes:***

- **Reader()** - constructor method
- **read()** - method reads file data into the uploader
- **close()** - for closing the reader at the end of the reading process


***The Reader object can process lines (split lines to cells) in two ways:***
- Using a separator token (or regex)
- Using a fixed set of widths provided in the fields configuration

To control which processing method to use, the reader constructor has a control flag that receives a **SplitMode** enum.

### 1.9.1 Reader constructor
Reader is created using **Reader()** constructor. It accepts data parsing related parameters (e.g. file path, desired schema etc.).

***Syntax:***

<reader> = Reader(file_path=<input_file_path>, schema=<table_schema>, separator=<regex>, type_selector =<selector>, include=<regex>, exclude=<regex>, split_mode=<SplitMode enum>)

***Returns:*** Reader object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **file_path** | String | Path to the input file. |
| **schema** | TableSchema | The schema with the fields configuration. |
| **separator** | String | A string that will be used to split the line to its field's values |
| **separator_regex** | String regex | The regex that will be used to split lines to their field’s values. |
| **type_selector** | FieldSelector/CustomSelector | Selector to determine record schema type (in case of multi record type input file). ***Default:*** **None** |
| **include** | String regex | Filter in the lines that should be included in the read data. ***Default:*** **None**|
| **exclude** | String regex | Filter out the lines that should not be included in the read data. ***Default:*** **None** |
| **split_mode** | SplitMode enum | Select in which mode the reader will split the lines from the input file (see [SplitMode enum definition](#166-splitmode-enum)).***Default:*** **SplitMode.separator**|


***Notes:***
- Supported compression formats for input file: **gzip** ('.gz'), **Zstandard** ('.zst').
- Either **separator** or **separator_regex** must be supplied.
- **separator** offers better performance than the separator_regex.
- Only lines that are **included** and not **excluded** will be read into the uploader.
- If **selector** is None, reader will try to use the schema’s nameless or single record type schema. If it doesn’t exist it will throw UploaderException.
- Passing a **separator** while using **SplitMode.fixed_width** mode will throw an exception.
- Using **SplitMode.fixed_width** reader with multiple record schemas is only possible when all of the schemas have the same structure i.e. all of the schemas are of the same size and for every field in a given index the width of the field is equal in all the schemas, otherwise an exception will be thrown.

 ***Code Example:***
``` py

# create a new TableSchema object using Field list parameter
schema = table_schema([…])
 
# include only lines that start with a digit (assuming time is the first field)
reader = Reader(file_path='my.log', schema=schema, separator='\|', include='^[0-9].**')

```

### 1.9.2 read method
Reader **read()** method is used to read data from the input file into the uploader system. It reads the data in batches, therefore it should be used in an iteration loop to ensure all the data is read. It throws **UploaderReadError** exception in case of reading errors. It accepts parameters for batch size and the number of errors to internally collect before throwing an exception (make it easy to fix bugs). The **read()** method returns DataTableCollection which is used to get each DataTable batch in an iteration loop. DataTable object then can be used to manipulate the data before writing it to the destination storage.

***Syntax:***

<data_table> = <reader>.read(batch_size=<lines_per_batch>, max_errors_per_batch=<num _errors >)

***Returns:*** DataTableCollection

Throws:  UploaderReadError exception

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **batch_size** | Number | Number of lines to read per read call. 10,000 |
| **max_errors_per_batch** | Number | Number of errors to internally collect per read before throwing an exception. ***Default:*** 0 (all) |

***Notes:***
- Throws UploaderException if number of read error exceeds the max_errors_per_batch value.
- See ErrorTable section for more info about read errors.

***Code Example:***
``` py

# create Reader
reader = Reader(…)
 
try:
    # iterate over batches, uses 10 line batch size until end of input file
    for table in reader.read(batch_size=10):
        # possibly iterate over each line in table and process it
except UploaderException as e:
    ...

```

### 1.9.3 close method
Reader **close()** method is used to finish the read and disconnect from the read input file.

***Syntax:***

<reader>.close()

***Returns:*** None

***Parameters:*** None

***Notes:***
- **close()** method is called automatically when exiting the reader construction scope.

***Code Example:***

``` py
# creating reader
reader = Reader(...)
reader.close()

```

## 1.10 UploaderReadError exception
**UploaderReaderError** is an exception object that is thrown from the Reader read method in case of a reading error. The Errors' information is stored in the ErrorTable object which is delivered in the exception object.

The exception is printable and will list all of the reading exceptions.

***UploaderReaderError related methods and attributes:***

- **error_table** - attribute to get the error table object

***Code Example:***
``` py

try:
    # iterate over batches
    for table in reader.read(...):
        ...
except UploaderReadError as e:
    print(e)

```

### 1.10.1 error_table attribute
UploaderReadError error_table attribute returns the ErrorTable object with the error information.

***Syntax:***

<error_table> = <read_error_exception>.error_table

***Returns:*** ErrorTable object

***Notes:***

***Code Example:***
``` py

try:
    # iterate over batches
    for table in reader.read(...):
        ...
except UploaderReadError as e:
    # get error table object
    error_table = e.error_table

```

## 1.11 ErrorTable object
The ErrorTable object contains a list of error information records. The error records are accessed by index. The specific error information is accessed by using dictionary style api

***Following are error dictionary keys:***
- **ERROR_NAME** - the error name
- **LINE_NUMBER** - the line number in which the error was found in the input file
- **ERROR_MSG** - the error details

***ErrorTable related methods and attributes:***
- **size** - attribute to get the number of errors in the table
- **[]** - operator to get a certain error record by index

### 1.11.1 size attribute
ErrorTable size attribute returns the number of error records in the ErrorTable.

***Syntax:***

<num_errors> = <data_table>.size

***Returns:*** number of error records in the ErrorTable object

***Notes:***

***Code Example:***
``` py

try:
    ...
except UploaderReadError as e:
    # get error table object
    error_table = e.error_table
 
    # get number of errors in the table
    num errors = error_table.size

```

### 1.11.2 [] operator
The **[]** operator is used to get a certain error record from the error table by index.

***Syntax:***

<error_record> = <error_table>[<error_index>]

***Returns:*** error record object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| error_index | Number | The index of the error record. Between 0 and <error_table>.size - 1 |


***Notes:***

***Code Example:***
``` py

try:
    ...
except UploaderReadError as e:
    # get error table object
    error_table = e.error_table
    # access error records by index
    for err_i in range(error_table.size):
        err_rec = error_table[err_i]
        # print error information
        Print(err_rec['ERROR_NAME'], err_rec['LINE_NUMBER'], err_rec['ERROR_MSG'] )

```

## 1.12 Writer object
The Writer is used to write data to some storage (currently support UTDB). The Writer is constructed using the Writer constructor, and the data is written using the write method. The write method can take as input - a DataTable, or a reader object internally used to read data. Then, write it directly to output storage without user interaction with the data.

***Writer related methods and attributes:***
- **Writer()** - constructor method
- **open_utdb()** - configure utdb target location. used with empty constructor.
- **open_text()** - configure text target location.
- **init()** - initialize writer object with the target table schema. Used with write_row method.
- **write()** - writes data into the output storage.
- **write_row()** - writes a single record into the output storage
- **close()** - for closing the writer and the connection to the destination storage

### 1.12.1 Writer constructor
The Writer is created using **Writer()** constructor. The Writer can be created without any target, and then add UTDB and/or text targets.

The **Writer()** constructor can also accepts a UTDB storage connection string as destination target.

The UTDB target connection string includes the path to the destination UTDB and potentially also the storage type.  

***Syntax:***

Create Writer without any target

<writer> = Writer()

Create Writer with UTDB target

<writer> = Writer(<connection_string>, [, fail_if_exists=<bool>])

<connection_string> => '[<db_type>:]<data_dest_path>'

***Returns:*** Writer object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| db_type | String | The data source type. ***Default:*** is set by **config.general.default_backend**. see [Supported UTDB storage types](#167-utdb-storage-types)) |
| data_dest_path | String | The path to where the trace data will be stored. |
| fail_if_exists | Bool | If the parameter is set to True, then if the data destination path already exists, the creation of a new writer will fail. If set to False, it will override the existing path and store the trace instead. ***Default:*** False |


Supported values: logdb, pg, pgpqt

Note: when multiple data source types will be supported, it will be possible to add different data source types.

***Code Example:***
``` py

# create new Writer object
writer = Writer('my_utdb_path')

# create new Writer for specific storage type
writer = Writer('pgpqt:my_utdb_path')

```

### 1.12.2 open_utdb method 
The Writer **open_utdb()** method configures UTDB output location. It accepts a storage connection string that includes the path to the destination file(s) and potentially also the type of the storage.
UTDB Writer can have only one UTDB output configuration, so if one already exists an error will be reported

***Syntax:***

<writer>.open_utdb(<connection_string> [, fail_if_exists=<bool>])

<connection_string> => '[<db_type>:]<data_dest_path>'

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| db_type | String | The data source type. ***Default:*** is set by **config.general.default_backend**. see [Supported UTDB storage types](#167-utdb-storage-types)) |
| data_dest_path | String | The path to where the trace data will be stored. |
| fail_if_exists | Bool | If the parameter is set to True, then if the data destination path already exists, the creation of a new writer will fail. If set to False, it will override the existing path and store the trace instead. ***Default:*** False |

***Notes:***
- **open_utdb()** method should be used only with writer that was created with empty constructor, otherwise an exception we be raised. 
- **open_utdb()** method needs to be called before the **init()** method is called

***Code Example:***
``` py

# create new Writer object using empty constructor
writer = Writer()
# set UTDB writing target 
writer.open_utdb('my_utdb_path')

```

### 1.12.3 open_text method 
The Writer **open_text()** method configures text output location and text table generation related parameters.
UTDB Writer can have only one text output configuration, so if one already exists an error will be reported

***Syntax:***

<writer>.open_text(<path> [, hide_metadata=<bool>] [, condensed_format=<bool>] [, page_size=<number>>] [,hierarchical=<bool>][,vertical_headers=<bool>])

***Returns:*** None

***Parameters:***

| Parameter Name | Type   | Description |
| -------------- | ----   | ----------- |
| path           | String | The path to where the text file will be stored. |
| hide_metadata  | Boolean   | Print record-type as a column and header of record type or not. Record type all header is always printed. If there is exactly one nameless record-type, then record-type is never printed even if hide_metadata is set to false. ***Default:*** **False** |
| condensed_format | Boolean | If True, will print in condensed (overlapping) mode (as in old Venus GUI). If False, will print in spreadsheet mode (as in new UTDB GUI). ***Default:*** **False** |
| page_size | Number | Print the title every page_size rows. Zero for printing the title once at the beginning. WARNING: it can cause to out of memory error when having a lot of rows. ***Default:*** 100 |
| hierarchical | Boolean | Print additional columns to the left of the table visualizing a tree structure of records. Leaves in the tree are marked with '-' character, and internal nodes (including tree roots) with '+' character. Character is indented according to the record's depth in the tree. ***Default:*** **False** |
| vertical_headers | Boolean | print headers vertically based on the width of data in the column. ***Default:*** **False** |

***Notes:***
- **open_text()** method needs to be called before the **init()** method is called

***Code Example:***
``` py

# create new Writer to write *only* text
writer = Writer()
# set text writing target 
writer.open_text('my_text_path') 

# create new Writer to write both UTDB and text
writer = Writer('my_utdb_path')
# set text writing target 
writer.open_text('my_text_path') 

```

### 1.12.4 init method
The Writer **init()** method is used to set the TableSchema of the writer directly. Calling the init method is not necessary if the writing is done only with the write method, since the Reader/DataTable object passed to **write()** method includes the TableSchema. If the **write_row()** method is used, then TableSchema needs to be set in the Writer object first.

***Syntax:***

<writer>.init(<schema>)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| schema | TableSchema | A TableSchema object containing table fields' information and configuration. Cannot be changed after execution of init. |

***Notes:***
- **init()** method needs to be called after the Writer targets were defined (via open_*() or constructor() methods) 

***Code Example:***
``` py

# define list of fields
fields = [
    field(name='DATA0', type=FieldType.STRING),  
    field(name='HIGH_PERFORMANCE', type=FieldType.STRING)
    ]
# add named RecordSchema with list of Fields
schema.add_record_schema('my_record_type', fields)
 
# create a new writer object
writer = Writer('my_utdb_location')
 
# initialize writer with the table schema
writer.init(schema)

...

```

### 1.12.5 write method
Writer **write()** method is used to write data to the configured destinations as defined in the Writer. It can be called multiple times with a DataTable object until all data is written, or a single time with a Reader object to internally read and write data to the configured destinations.

when using hierarchical schema for the data it cannot be used with a Reader object.

***Syntax:***

<writer>.write(<data_table>)

<writer>.write(<reader> [, batch_size=<num_lines>])

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| data_table | DataTable | Data table object ready to be written |
| reader | Reader | Reader object configured to read data |
| **batch_size** | Number | Number of lines to read per read call. ***Default:*** 10,000 |

***Notes:***
- Throws UploaderException if number of read errors exceeds the max_errors_per_batch value.
- Throws Exception if Writer output targets were not defined

***Code Example:***
``` py
 
# create writer with storage path
writer = Writer('my_utdb_location')   # use Writer write() directly from Reader
 
# write data to UTDB from Reader
# create data reader
reader = Reader(…)
writer.write(reader)
 
# write data to UTDB from Flat DataTable
for table in reader.read(…):
    # possibly iterate over each line in table and process it
    writer.write(table)

writer.close()
  
# create hierarchical schema
schema = table_schema(hierarchical=True)

# create data table
table = DataTable(schema)
hier = table.is_hierarchical() # Returns True
 
# add child records
root = table.add_record()
child_1 = root.add_record()
child_2 = root.add_record()
 
# create writer with path to output UTDB
writer.write(table)

writer.close()

```

### 1.12.6 write_row method
Writer **write_row()** method is used to write a single record to the configured destinations as defined in the Write. The **write_row()** method can be called multiple times to inject records separately, or in tandem with the use of **write()** method. The record is provided to **write_row()** either as a list, a dictionary of key=value parameters. Writer object must be initialized with a table schema before using the **write_row()** method.

***Syntax:***

<writer>.write(<row_dict> | <row_list> | <kargs> [,<record_type>])

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| row_dict    | Dict | Keys are field names as defined in the schema. Values are of primitive python types (number/string/boolean). |
| row_list    | list or tuple | list of primitive python types. Values must be in the order of fields as defined in the schema. |
| kargs       | Key=value args | Keys are field names as defined in the schema. Values are of primitive python types (number/string/boolean). |
| record_type | String | The name of the record type as defined in the schema. Empty if schema has only a nameless record type or a single named record type. |

***Notes:*** 
- Writer object must be initialized with a table schema before using **write_row()**. This can be done in one of the following methods:
    - Calling **init()** method with the schema before the first **write_row()** call.
    - Calling **write()** method with a DataTable of the appropriate schema before the first write_row call.
- Throws UploaderException if the values or keys in the row do not correspond to the initialized table schema.

***Code Example:***
``` py

# create a new TableSchema object using Field list parameter
schema = table_schema()
 
# define list of fields
fields = [
    field(name='TIME', type=FieldType.INT),
    field(name='DATA', type=FieldType.STRING),  
    field(name='FLAG', type=FieldType.BOOL)
    ]
# add named RecordSchema with list of Fields
schema.add_record_schema('my_record_type', fields)
 
# create writer with path to output UTDB
writer = Writer('my_utdb_location')
 
# initialize writer with the tableSchema
writer.init(schema)
 
# use Writer write_row() to inject a record to the configured output
writer.write_row([1, 'some string', True], record_type='my_record_type')  # use complete list of values
writer.write_row([2, 'other string'], record_type='my_record_type')       # use partial list of values. field FLAG left empty (null value)
writer.write_row({'TIME':3, 'FLAG':False}, record_type='my_record_type')  # use dictionary of field:value. field DATA left empty (null value)
writer.write_row(TIME=3, FLAG=False, record_type='my_record_type')        # use Key=value args. field DATA left empty (null value)
 
# close writer
writer.close()

```

### 1.12.7 close method
Writer **close()** method is used to finish the writing and disconnect from the output storage.

***Syntax:***

<writer>.close()

***Returns:*** None

***Parameters:*** None

***Notes:***
- close method is called automatically when exiting the writer construction scope.

***Code Example:***
``` py

# creating writer
writer = Writer(...)

# ...

writer.close()

```

## 1.13 upload method
**upload()** global method reads the data from the textual trace using Reader and writes the UTDB table.

***Syntax:***

upload(reader=<reader> [,writer=<writer>] [,record_editor=<record_editor_function>])

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **reader** | Reader | The Reader object that was initialized for reading |
| **writer** | Writer | The Writer object that was initialized for writing. (optional). ***Writer Defaults:*** out dir: current working dir as, utdb_name: input log file nae with “_utdb” replacing log/gz postfix |
| **record_editor** | Function | Function pointer to a record processing function that will be applied on records after reading. Signature : “def record_editor(record)”. ***Default:*** None |

***Code Example:***
``` py

# Writing with the Reader
# create data reader
reader = Reader(...)
 
# create writer with path to output UTDB
writer = Writer('my_utdb_location')
 
# create a record editing function
def record_editor(record):
    if record["DATA"] is None:
        record["DATA"] = "DATA_" + str(record["LINE_NUM"])
 
# read the data from textual trace and write to UTDB storage
upload(reader=reader, writer=writer, record_editor=record_editor)

```

## 1.14 Discover schema method
**discover_schema()** creates a TableSchema by reading #header from the textual trace.

The fields' names and record types are extracted from #header. The type of the fields will be STRING, if there is a field named "time" its type will be INT.

***Syntax:***

discover_schema(file_path=<input_file_path> [,schema_overrides=<schema_overrides>])

***Returns:*** TableSchema

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| **file_path** | String | Path to the input file |
| **schema_overrides** | Dictionary of string and field object | Dictionary with a key of string - represents the original field name from the #header and a field object. Used to override the default name and type. ***Default:***  **None**|

***Code Example:***
``` py

# create schema overrides dictionary
schema_overrides = {
    "Time": field(name="TIME", type=FieldType.UINT),
    "data": field(name="DATA", type=FieldType.BOOL),
    "TID" : field(name="TID", type=FieldType.UINT)
}
 
# create schema using discover_schema
schema = discover_schema(file_path='my_file.log', schema_overrides=schema_overrides)

```

------------------------------

# 2 Trace and Metadata

Data from a single UTDB storage is represented by a Trace object. Trace objects are obtained from calls to **connect()** and are used in a variety of contexts: to explore the schema of the data, to construct queries, etc. This section describes the Trace object API and related global methods.

## 2.1 connect()
Trace objects are obtained using the global **connect()** function. The data to connect to is identified by a connection string.

The connection string represents the location of the source data and optional parameters required to start working with that data. In the most general case, the connection string has a URI syntax:
```
[storage-type:]path[?storage-specific-params]
```
The *storage-type* part of the connection string is one of the [Supported UTDB storage types](#167-utdb-storage-types). The *storage-specific-params* depend on the specific storage type and are documented below for those storages for which they are applicable.

For most cases, assuming UTDB data exists on a file system, the connection string may just be the full directory path of the UTDB. The type of storage will be detected automatically in such case.

***Syntax:***

<trace> = connect(connection_string, record_type_name_case=<name case>, field_name_case=<name case>)

***Returns:*** Trace object

***Parameters:***

| Parameter Name | Type | Description | 
| -------------- | ---- | ----------- |
| connection_string | String | The connection string identifying the data to connect to and optional connection parameters. |
| record_type_name_case | NameCase | Record type name case. Default: NameCase.LOWER |
| field_name_case | NameCase | Field name case. Default: NameCase.UPPER |

***Notes:***
- See [Supported UTDB storage types](#167-utdb-storage-types).
- Supported compression formats: **gzip** ('.gz'), **Zstandard** ('.zst').
- UTDB storages from older versions do not support automatic identification of the *storage-type*. In such cases, if *storage-type* is not explicitly specified in the connection string, it is determined by the value configured in UTDB.config.general.default_backend, which has a default value of "logdb".

### 2.1.1 Connecting to logdb, pgpqt, pg storage
Connection strings for logdb, pgpqt, pg storage types do not currently support any *storage-specific-params*. The connection to these storages may be done by only specifying the path to the storage location on disk: the same path that was specified in the connection string of the uploader with which the data was created. The type of the storage will be detected automatically, so specifying it is unnecessary in most cases (but possible).

***Code Example:***
``` py
# connect to a trace, automatically identifying the type of the storage
trace = connect('/nfs/site/.../path_to_utdb')
```

### 2.1.2 Connecting to pgjem storage
Connecting to Jem traces supports connecting to a single trace or to multiple traces simultaneously, using "pgjem" storage-type identifier.

When connecting to a single Jem trace storage, the *path* component of connection string should refer to a single Jem trace index file. The storage-type may be identified automatically.
``` py
# connect to Jem trace, automatically identifying the type of the storage
trace = connect('/nfs/site/.../path/to/jem/trace/index/file')

# connect to Jem trace, explicitly specifying the storage type
trace = connect('pgjem:/nfs/site/.../path/to/jem/trace/index/file')
```
This storage types supports additional storage-specific parameters which may be specified after the ?-mark in the connection string. All parameters after the ?-mark are separated by semicolons. Parameters that have values are written as param=values. A parameter may have multiple values separated with '+'. Each part of the connection string may be properly double-quoted to avoid any parsing ambiguity.

| Param | Description | 
| -------------- | ----------- |
| dbso=<libtlmgen_db1.so>+<libtlmgen_db2.so>+... | One or more paths to Jem-generated shared library with _db in the name, which are needed to interpret the data in the trace. These libraries are typically located in the model build output area. UTDB/Jem will try to automatically identify that location based on the information present in the trace, but it may not always be possible (e.g. if the files were moved to a different location). Multiple paths may be provided, separated by plus-sign '+'; or, the param may be specified multiple times. |
| src=<src.1>+<src.2>+... | If specified, limits the trace data to that originating only from the specified sources: only data of those sources will be loaded. Sources are usually identified by their full RTL paths in the simulation model, such as "mytop.mysub.myip.mymonitor.port_a". A perl-style regular expression enclosed in parentheses may be used. Use double-quotes to avoid parsing ambiguities when using various special characters. Multiple values may be provided, separated by plus-sign '+'; or, the param may be specified multiple times.|

***Notes:***
- In the current version, connecting to a Jem trace requires the trace to be recorded in one of the following formats. Configuration of the trace format during recording is controlled by Jem's environment variable $JEM_TLM_TRACE_FORMAT. It should be set to one of the above values. See Jem documentation for more details.
    - x64_indexed_var_size_multi_source_format (recommended for simulation)
    - x64_fixed_size_multi_source_format
    - x64_fixed_size_single_source_format (required for emulation)

***Code Example:***
``` py
# connect to Jem trace with extra parameters
trace = connect('/nfs/mytrace/tlm_trace_index.txt?dbso=/nfs/…/jem/models/mymodel/libtlmgen_db.so;src="(.*my_ip_1.*)"+"(.*my_ip_2.*)"')
```

#### 2.1.2 Connecting to multiple Jem traces

Connecting to multiple Jem traces simultaneously is an adanvced usage. With current Jem versions, this is limited to traces of the same model, such as in case of multiple tests of the same DUT, or in case of multi-process simulations where the a model is co-simulated with another copy of the same model.

When connecting to multiple Jem traces simultaneously, the *storage-type* "pgjem" must be explicitly specified in the connection string. The *path* component should contain multiple entries, separated with plus sign '+'. Each entry should be of the form
```
tracename@/path/to/trace/index/file
```
where each of the traces should have a unique *tracename*. This *tracename* will appear as a prefix of all sources (rtl-paths of monitors) coming from the given trace storage.

***Code Example:***
``` py
# create a Jem trace with type specific parameters
trace = connect('pgjem:trace1@/a/b/c/trace/index+trace2@/x/y/z/trace/index?src="(.*my_ip_1.*)"+"(.*my_ip_2.*)"')
```

## 2.2 describe()
The global function describe() prints out all kinds of useful information about a trace, including its schema.

***Syntax:***

describe(trace [, verbose=<True|False>])

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| trace | Trace object | Trace, previously obtained from **connect()**. |
| verbose | Boolean | If True, prints out extra information. ***Default:***  **False** |

***Code Example:***
``` py
trace = connect(utdb_path)
describe(trace)
 
# Example output
# -N- [UTDB]: UTDB version 23.02p1
# Trace (repetition_example_utdb)
# Record type "all" fields:
#     1) TIME: int64
#     2) OP: string
#     3) TID: string
```

## 2.3 Trace object
Trace object represents the data from a single UTDB storage. It provides access to the metadata associated with that storage: the record types, the fields, etc. existing in the trace. All fields of the trace are accessible via a built-in record type named "all". Other record types might have been defined in the trace, in which case they are accessible by name from the Trace object.

***Related methods:***
- **connect()**: a global function to connect to a UTDB storage and obtain a new Trace object.
- **describe()**: a global function to print out useful informational details about a trace.

***Attributes:***

| Name | Description |
| ---- | ----------- |
| record_types | List of RecordTypeDescriptor objects representing all record types in the trace. |
| all | A built-in record type that contains all fields in the trace. |
| *<record -type-name>* | Each user-defined record type is accessible as attribute of the Trace object by name. |

### 2.3.1 Trace.record_types
A list of the RecordTypeDescriptor objects existing in the Trace.

***Syntax:***

<record_type_list> = <trace>.record_types

***Returns:*** list of RecordTypeDescriptor objects

***Notes:*** 

***Code Example:***
``` py
# get record type names list
rt_list = trace.record_types
print([x.name for x in rt_list])
 
# output example
['all', 'req', 'resp']
```

### 2.3.2 Trace.all
The built-in record type **all**. This record type contains all the fields from all the record types in the trace. It can be used to reference any field regardless of its record type.

***Syntax:***

<record_type_descriptor> = <trace>.all

***Returns:*** RecordTypeDescriptor object

***Notes:*** 

***Code Example:*** 
``` py
# get record type names list
all_rec_type = trace.all
```

### 2.3.3 Trace.*<record_type_name>*
User defined record types, if defined during uploading, are accessible by name as attributes of the Trace object (usually, in lower-case letters).

***Syntax:***

<record_type_descriptor> = <trace>.<record_type_name>

***Returns:*** RecordTypeDescriptor object

***Notes:*** 

***Code Example:***
``` py
# get record type descriptor
rec_type = trace.my_record_type
```

### 2.3.4 Trace.connection_string()
This method returns the connection string that the Trace object was created with.

**Syntax:**

<string> = <trace>.connection_string()

**Returns:** String

**Code Example:**
```
# get connection string
conn_string = trace.connection_string()
```

## 2.4 RecordTypeDescriptor object
RecordTypeDescriptor object represents collection of fields. In case of a built-in record type **all**, that would be a collection of all fields of the trace. In case of user-defined record type, that would be a subset of those fields. RecordTypeDescriptor provides access to the fields as attributes by name, or as an iterable container of all fields.

***Related methods:***
- **name()**: a global function to obtain the name of the record type
- **record_type_fields()**: a global function to obtain an iterable over fields in the record type

***Attributes:***

| Name | Description |
| ---- | ----------- |
| fields | List of all Field objects in the record type. |
| *<field -name>* | Each Field is accessible as attribute of the RecordTypeDescriptor object by name. |

### 2.4.1 RecordTypeDescriptor.fields
A sequence of Field objects in the record type. This created object is a duplicate of the record type's field list which can be freely modified by the user.
This includes operations such as removing, replacing, and renaming fields by their names, as well as inserting or deleting fields by their index.

***Syntax:***

<field_descriptor_list> = <record_type_descriptor>.fields

***Returns:*** Collection of Field objects

***Attributes enabling Field manipulations by name:***

| Name | Description |
| ---- | ----------- |
| get  | Retrieves a Field object by its name if it exists within the collection. If a Field with the specified name does not exist, a KeyError exception is raised.|
| remove  | Removes a Field object from  collection by its name. If a Field with the specified name does not exist, a KeyError exception is raised.|
| replace  | Replaces an existing Field object with a new Field object. If a Field with the specified name does not exist, a KeyError exception is raised. If a Field with new name already exists in the collection, InvalidArgument exception is raised |
| rename  | Renames a Field with name 'A' to name 'B'. IF a Field with name 'A' does not exist, a KeyError exception is raised. If a Field with name 'B' already exists in the collection, InvalidArgument exception is raised |

***Notes:*** This object supports most standard list operations, such as iteration, the **in** operator, accessing elements by index. 

***Code Example:***
``` py
# get record type names list
field_list = trace.all.fields
print([x.name for x in field_list])
 
# output example
['RECORD_TYPE', 'TIME', 'ADDR', 'DATA', 'OPTYPE', 'UOP']

if 'DATA' in field_list:
    field_list.remove('DATA')
field_list.append(output_field('DATA_LOW', trace.all.DATA[4:0]))
field_list.insert(1, output_field('SRC', 'my_src'))
field_list.replace('ADDR', output_field('ADDR_HIGH', trace.all.ADDRESS[16:8]))
print([x.name for x in field_list])

# output example
['RECORD_TYPE', 'SRC', 'TIME', 'ADDR_HIGH', 'OPTYPE', 'UOP', 'DATA_LOW']
```

### 2.4.2 RecordTypeDescriptor.*<field_name>*
Individual Field objects are accessible by name as attributes of the RecordTypeDescriptor object (usually, in upper-case letters).

***Syntax:***

<field_descriptor> = <record_type_descriptor>.<field_name>

***Returns:*** Field object

***Notes:***
- Special semantics in **where()** and **detect()**: such usage of field implies that condition relates to only extended record type of referenced record type. In other words, condition will be satisfied only if record has record type that extends referenced record type.

***Code Example:***
``` py
# get field
field = record_type.FIELD_NAME
```

## 2.5 Field object
Field represents a specific field. This object may participate in expressions in order to construct queries.

***Related methods:***
- **name()**: a global function to obtain the name of the field

***Attributes:***

| Name | Description |
| ---- | ----------- |
| name | The name of the field. |
| type | The data type of the field. |

### 2.5.1 Field.type
The data type of the field, one of the supported Data Types described in [DataType enum](#28-datatype-enum).

***Syntax:***

<data_type> = <field>.type

***Returns:*** DataType enum value

### 2.5.2 Field.name
The name of the field.

***Syntax:***

<name> = <field>.name

***Returns:*** String

## 2.6 name()
The global function **name()** may be used to obtain the name of various objects, such as a RecordTypeDescriptor, or a Field.

***Syntax:***

<name> = name(<record_type_descriptor>)

<name> = name(<field>)

***Returns:*** String

## 2.7 record_type_fields()
A sequence of Field objects in a record type.

***Syntax:***

<field_list> = record_type_fields(<record_type_descriptor>)

***Returns:*** sequence of Field objects

## 2.8 DataType enum
DataType enum lists the valid value data types in UTDB traces.

***Enum Values:***

| Enum Value | Description | 
| -------------- | ---- |
| DataType.BOOL | Boolean value (True, False) |
| DataType.INT | 64bits signed integer  |
| DataType.UINT | 64bits unsigned integer |
| DataType.AINT | arbitrary size integer |
| DataType.DOUBLE | floating point number |
| DataType.STRING | string |
| DataType.OPAQUE | OPAQUE values are extracted from non SQL storages (e.g. JemDB) |


------------------------------

# 3 UTDB Expressions
A native Python Expression is a python expression evaluated to a value by the Python interpreter.

UTDB expression is a python expression that includes UTDB elements (coming from trace object) and methods, and is checked and evaluated in the underlying query mechanism.

- A field expression, or a bit-slice of such
- A computed field, such as a result of output_field()
- A parameter, such as a result of bindparam()
- Application of a built-in operator or function on operand sub-expression(s)
- Other value expression in parentheses (used to group sub-expressions or override precedence)

Expressions can have a special null value, which indicates absence of a value. Note that for some data types, which also have a notion of “empty value”, such as strings, the null value is not the same as the empty value. A null value of a boolean condition used in query-constructing functions, such as **where()**, is treated as false.

***Note:***
In this section we will refer Field as Field and RecordTypeDescriptor as RecordType

## 3.1 Field Expressions

### 3.1.1 Field

Fields of records can be referred to in expressions by using the Field

***Syntax:***

<field_expr> = <trace>.<record_type_name>.<field_name>

***Returns:*** UTDBExpression object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| trace | Trace  | trace created by connecting to UTDB. |
| record_type_name | String | The RecordType name that is accessed as attribute under the Trace object |
| field_name | String | The Field name that is accessed as attribute under the RecordType object |

***Code Example:***
``` py

# create a trace
trace = connect(…)
 
#create Field Expression of record type ‘resp’
f1 = trace.resp.FIELD1
 
#create Field Expression of any record type
f2 = trace.all.FIELD2

```

### 3.1.2 output_field method
The **output_field()** method is used to specify a new user-defined field. OutputField can be used as Field and UTDB expressions. The user should specify a legal field name and a UTDB expression (with using original field) to get the required value from the UTDB database. In addition, the displayed field format can be controlled (as in the schema field method).

***Syntax:***

<field_expr> = output_field(<field_name> , <value_expression> [, format=<format_string>] [, display_name=<string>])

***Returns:*** Field object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| field_name | String | The name of the new field. |
| value_expression | UTDB Expressions | Expression to calculate the value of the new field |
| **format** | string | python style format_string |
| **display_name** | string | A unique name to use as header name in **dump()** API  |

***Notes:***

- The expression can be a UTDB expression or a python expression.
- The field type is inferred from the value expression. 

***Code Example:***
``` py

# select two fields to be obtained
query1 = fields(output_field("NEW_FIELD" , trace.all.FIELD1 + trace.all.FIELD2, format='{:#X}'))

```

## 3.2 Slice operator
Slice operator **[]** enables the user to refer to a bit slice of an integer numeric expression, or to a substring of a string expression. Indexes are 0-based, where the least significant bit of the value is the bit 0 for numeric expressions.

A string operator can be applied to expressions with unknown type as well (e.g. when it is applied to expressions that contain flow variables), yet it will fail if the evaluated expression is not integer numeric or string.

***Syntax:***

Numeric fields:

<utdb_num_expr> = <utdb_num_expr>[bit_index] - bit_index is a non-negative integer

<utdb_num_expr> = <utdb_num_expr>[MSB:LSB] - MSB and LSB are non-negative integers

String fields:

<utdb_str_expr> = <<utdb_str_expr>>[index] - index is an integer. Negative values are interpreted as reverse index from end of string

<utdb_str_expr> = <<utdb_str_expr>>[start:stop] - start and stop are optional integers. If start is not provided then start is 0. If end is not provided then end is -1. Negative values are interpreted as reverse index from end of string

***Returns:*** UTDBExpression object, Null if one or more of the indexes is out of bound.

***Code Example:***
``` py

# create a trace
trace = connect(…)
 
#create single bit Slice expression
trace.req.ADDR[3]
 
#create single character Slice expression
trace.req.OPCODE[3]
 
# create arithmetic expression with slice operands
trace.req.ADDR[8:4] + trace.req.DATA[4:0]
 
# create expression with range slice
trace.req.OPCODE[0:3]

```

## 3.3 Built-in operators
The following standard operators are supported with their natural semantics (except Python bitwise operators which are overloaded as logic ones). Their applicability to data types is as usual in Python. Their precedence is dictated by Python rules.

| Category | Syntax | Return object | Notes |
| -------- | ------ | ------------- | ----- |
| Comparison | == , != | Boolean Expression | Applicable for all DataTypes. |
| Comparison | < , <= , > , >= | Boolean Expression | Applicable for numeric DataTypes. |
| Arithmetic | - , * , / , % | Value Expression | Applicable only for numeric DataTypes. |
| Arithmetic | + | Value Expression | Applicable for numeric (+) and strings (concatenation). |
| Logical | & , \| , ~ | Boolean Expression | Python bitwise operations are overloaded as logical ones. |

Operators invoked on native Python expression are evaluated by Python as usual. An expression that includes at least one non-native operand is evaluated in the underlying query mechanism.

Arithmetic, bitwise, and comparison operators on null values produce null. Logical operators produce null only if the result is undecidable. E.g. “true & null” produces null; while “true | null” produces true.

***Code Example:***
``` py

# create trace
trace = connect(…)
 
# arithmetic expressions
trace.req.DATA - 0xA0
1000 * trace.resp.ADDR
trace.req.DATA % 4 + 0xA0
trace.req.OPCODE + trace.req.DEST
 
# comparison expressions
trace.req.DEST == 'CPU'
trace.resp.ADDR < 0x123
trace.req.ADDRESS > (trace.req.DATA + 0xA0)
 
# logical expressions
e1 = (2000 < trace.all.TIME)
e2 = ~e1                            #logical NOT
e2 | (trace.req.OPCODE == ‘READ’)   #logical OR
(trace.resp.ADDR[3:2] > 5) & e1      #logical AND

```

## 3.4 Built-in functions

### 3.4.1 Functions on operands of all DataTypes

#### 3.4.1.1 exists method
**exists()** method returns **True** iff <field_expr> has a non-null value

***Syntax:***

<bool_expr> = <field>.exists()

***Returns:*** Boolean Expression

#### 3.4.1.2 not_exists method
**not_exists()** method returns **True** iff <field> does not have a value (equivalent to has null-value)

***Syntax:***

<bool_expr> = <field>.not_exists()

***Returns:*** Boolean Expression

#### 3.4.1.2 in_list method
**in_list()** method compares expression with multiple values. It returns **True** iff <expression> is equal to one of the values in the list.

***Syntax:***

<bool_expr> = in_list(<expression>, <list_of_values>)
<bool_expr> = <expression>.in_list(<list_of_values>)

***Returns:*** Boolean Expression

### 3.4.2 Functions on String Expressions (string matching operators)

#### 3.4.2.1 match method
**match()** method returns **True** iff string <expression> matches <pattern>, which can be a regex or a wildcard (a string with * matching any sequence of zero or more characters).

***Syntax:***

<bool_expr> = match(<str_expr>, <pattern> [, ignore_case=[True|False]] [, kind=['regex'|'wildcard']])

<bool_expr> = <str_field>.match( <pattern> [, ignore_case=[True|False]] [, kind=['regex'|'wildcard']])

***Returns:*** Boolean Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| str_expr | String | value String to search in  |
| str_field | Field | Field of DataType STRING to search in |
| pattern | String | Pattern string to search for |
| **ignore_case** | Boolean | indicate if to ignore string case or not |
| **kind** | Boolean | indicate if the pattern is 'regex' style or 'wildcard' |

***Code Example:***
``` py

output_field("MATCH_REGEX_VALUE",  match(trace.all.RECORD_TYPE,".*req.*")),

```

#### 3.4.2.2 contains method
**contains()** method returns **True**  iff the string <expression>/<field> value contains a string <substring>

***Syntax:***

<bool_expr> = contains(<str_expr>, <substring> [, ignore_case=[True|False]] )  
<bool_expr> = <str_field>.contains( <substring> [, ignore_case=[True|False]] )

***Returns:*** Boolean Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| str_expr | String | value String to search in  |
| str_field | Field | Field of DataType.STRING to search in |
| substring | String |  Substring to search for |
| **ignore_case** | Boolean | indicate if to ignore string case or not |

***Code Example:***
``` py

output_field("CONTAINS_RES",       contains(trace.all.RECORD_TYPE,"res")),

```

#### 3.4.2.3 begins_with method
**begins_with()** method returns **True**  iff the string <expression>/<field> value begins with a string <prefix>

***Syntax:***

<bool_expr> = begins_with(<str_expr>, <prefix> [, ignore_case=[True|False]] )  
<bool_expr> = <str_field>.begins_with( <prefix> [, ignore_case=[True|False]] )

***Returns:*** Boolean Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| str_expr | String | value String to search in  |
| str_field | Field | Field of DataType.STRING to search in |
| prefix | String |  prefix string to look for |
| **ignore_case** | Boolean | indicate if to ignore string case or not |

***Code Example:***
``` py

output_field("BEGINS_WITH_CPU",    begins_with(trace.all.RECORD_TYPE,"cpu")),

```

#### 3.4.2.4 ends_with method
**ends_with()** method returns **True** iff the string <expression>/<field> value ends with a string <suffix>

***Syntax:***

<bool_expr> = ends_with(<str_expr>, <suffix> [, ignore_case=[True|False]] )  
<bool_expr> = <str_field>.ends_with( <suffix> [, ignore_case=[True|False]] )

***Returns:*** Boolean Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| str_expr | String | value String to search in  |
| str_field | Field | Field of DataType.STRING to search in |
| suffix | String |  prefix string to look for |
| **ignore_case** | Boolean | indicate if to ignore string case or not |

***Code Example:***
``` py

output_field("ENDS_WITH_REQUEST",  ends_with(trace.all.RECORD_TYPE,"request")),

```

#### 3.4.2.5 extract method
**extract()** method returns a String that matches the pattern (or NULL). If the pattern contains any parentheses, the function returns the portion of the text that matched the first parenthesized sub-expression

***Syntax:***

<str_expr> = extract(<str_expr>, <pattern> [, ignore_case=[True|False]] )

***Returns:*** String value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| str_expr | String | value String to search in  |
| str_field | Field | Field of DataType.STRING to search in |
| pattern | String |  prefix string to look for |
| **ignore_case** | Boolean | indicate if to ignore string case or not |

***Code Example:***
``` py

output_field("EXTRACT_FULL_VALUE", extract(trace.all.RECORD_TYPE,"nb.*")),
output_field("EXTRACT_PART_VALUE", extract(trace.all.RECORD_TYPE,"(r.*)")),

```
       
#### 3.4.3 Functions on Numeric Expressions (bitwise operators)

| Function | Syntax | Return object | Evaluation result |
| -------- | ------ | ------------- | ----------------- |
| bit_and | bit_and(<num_expr>,<num_expr>) | Integer value | Returns bitwise AND for all bits of given values. |
| bit_or | bit_or(<num_expr>,<num_expr>) | Integer value | Returns bitwise OR for all bits of given values. |
| bit_xor | bit_xor(<num_expr>,<num_expr>) | Integer value | Returns bitwise XOR for all bits of given values. |
| bit_not | bit_not(<num_expr>) | Integer value | Returns bitwise NOT for all bits of given value. |
| bit_lshift | bit_lshift(<num_expr>,<offset>) | Integer value | Returns bitwise LEFT SHIFT for given value, i.e. shifts each bit in the given value to the left <offset> times. |
| bit_rshift | bit_rshift(<num_expr>,<offset>) | Integer value | Returns bitwise RIGHT SHIFT for given value, i.e. shifts each bit in the given value to the right <offset> times. |
| bit_ceil | bit_ceil(<num_expr>) | Integer value | Finds the smallest integral power of two - above the given value. |
| countl_zero | countl_zero(<num_expr>) | Integer value | Counts the number of consecutive 0 bits, starting from the most significant bit. |
| countr_zero | countr_zero(<num_expr>) | Integer value | Counts the number of consecutive 0 bits, starting from the least significant bit. |
| has_single_bit | has_single_bit(<num_expr>) | Boolean value | Checks if a number is an integral power of two. |
| bit_floor | bit_floor(<num_expr>) | Integer value | Finds the largest integral power of two - below the given value. |
| bit_width | bit_width(<num_expr>) | Integer value | Finds the smallest number of bits needed to represent the given value. |
| rotl | rotl(<num_expr>, <offset>) | Integer value | Computes the result of bitwise left-rotation <offset> times. |
| rotr | rotr(<num_expr>, <offset>) | Integer value | Computes the result of bitwise right-rotation <offset> times. |
| countl_one | countl_one(<num_expr>) | Integer value | Counts the number of consecutive 1 bits, starting from the most significant bit. |
| countr_one | countr_one(<num_expr>) | Integer value | Counts the number of consecutive 1 bits, starting from the least significant bit. |
| popcount | popcount(<num_expr>) | Integer value | Counts the number of 1 bits in an unsigned integer. |


#### 3.4.4 Global Functions

#### 3.4.4.1 record_type() method

**record_type()** method returns **True** iff the record is of the given record_type.

***Syntax:***

<bool_expr> = record_type(<record_type_descriptor>)

***Returns:*** Boolean Expression

***Parameters:***

| Parameter Name         | Type                 | Description                                         |
| ---------------------- | -------------------- | --------------------------------------------------- |
| record_type_descriptor | RecordTypeDescriptor | return true if record has the specified record type |

#### 3.4.4.2 record_type_extends() method
**record_type()** method returns **True** iff the record is of record type that extends given record type.

***Syntax:***

<bool_expr> = record_type_extends(<record_type_descriptor>)

***Returns:*** Boolean Expression

***Parameters:***

| Parameter Name         | Type                 | Description                                                              |
| ---------------------- | -------------------- | ------------------------------------------------------------------------ |
| record_type_descriptor | RecordTypeDescriptor | Return true if record has record type that extends specified record type |

#### 3.4.4.3 if_ method
**if_()** method get a condition and 2 expressions. It returns the first expression if the condition is True and the second expression otherwise

***Syntax:***

<expression> = if_(<condition>, <true_expr>, <else_expr>)

***Returns:*** UTDB Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| condition | Boolean Expression | condition to determine which expression to return |
| true_expr | UTDB Expression | expression to return if the condition is True |
| else_expr | UTDB Expression | expression to return if the condition is False |

***Code Example:***
``` py

output_field("INITIATOR",          if_(begins_with(trace.all.RECORD_TYPE,"cpu"),"CPU","OTHER")),

```

#### 3.4.4.4 switch method
**switch()** method returns the first value for which <key> evaluates as equal to <expression>. Otherwise returns default_value

***Syntax:***

<expression> = switch(<comp_expr>, cases={<key>:<expression>  [, <key>:<expression> ...] } [, default=<default_expression> ])

***Returns:*** UTDB Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| comp_expr | UTDB Expression | expression to check <keys> against  |
| **cases** | Dict of key:value | keys are checked against comp_expr and if it matches it returns the expression |
| **default** | UTDB Expression | in case none if the keys match, it return the default expression |

***Code Example:***
``` py
mem_region_mapping = {
    0x1 : "LOW_MEM1",
    0x2 : "LOW_MEM2",
    0x3 : "LOW_MEM3",
    0xa : "HIGH_MEM1",
}

output_field("SWITCH_MEM", switch(trace.all.ADDRESS[28:32], cases=mem_region_mapping)),

```

#### 3.4.4.5 first_non_null method
**first_non_null()** method returns the first expression from list that does not evaluate as null. otherwise returns null

***Syntax:***

<expression> = first_non_null(<expression_1>, [, <expression_2>, ...] )

***Returns:*** UTDB Expression

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| expression_X | UTDB Expression | expressions to evaluate. The first one that will NOT evaluated None with be returned |

***Code Example:***
``` py

output_field("COREREQID_OR_DELAY", first_non_null(trace.all.COREREQID, trace.sbresponse.DELAY))

```

#### 3.4.5 Expressions examples

***Code Example:***
``` py

# create trace
trace = connect(…)
 
# null checking
trace.req.DATA.exits()
trace.req.OPCODE.not_exists()
 
# string matching
match(trace.resp.OPCODE + trace.resp.DEST, ‘^re.*dest$’, kind=’regex’)
trace.all.UNIT.contains(‘ia_0’, ignore_case=True)
 
# record type expression
record_type(trace.req)
 
# mixed expressions
# ** DATA is not null for records of type ‘req’
record_type(trace.req) & (trace.all.DATA.exists())
 
# ** DATA is less than 123 and 1) for records of type ‘req’ OPCODE contains ‘GO’ or 2) for records of type ‘resp’ OPCODE starts with ‘Wr’
(trace.req.OPCODE.contains(‘GO’) | trace.resp.OPCODE.begins_with(‘Wr’)) & (trace.all.DATA <123)
 
 
# get a string that starts with 'R', ends with 'd' and as other letters in between (possibly 'Read')
extract(trace.cpurequest.OPCODE, 'R\s*\w+d')
 
# comparison expressions with multiple values
trace.all.TIME.in_list([1000, range(2000,3000), 5000])  # numeric value from list
in_list(trace.req.DEST+'ABC', ['XABS', 'YABC', 'ZABC']) # string value from list

```

## 3.5 Casting functions
UTDB casting function can be used to change fields' or expressions' data type from number to string or vice versa. In practice they are used in output_field (Define user output fields section below) to create a user defined field. In addition, conversion parameters such as number base, upper/lower case string, and include/exclude base prefix can be set.

### 3.5.1 to_str method
The **to_str()** method converts its operand to a string.

***Syntax:***

<string> = to_str(<expr>)

***Returns:*** String

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| expr | UTDB Expression | On numeric types produces a decimal string representation, and on string data type produces the same value. |

***Notes:***

***Code Example:***
``` py

# convert OPCODE number to a decimal number string field
output_field('OPC_STR', to_str(trace.all.OPCODE))

```

### 3.5.2 to_int, to_uint and to_aint method
The **to_int()**, **to_uint()** and **to_aint()** methods are used to convert a string that represent a number to a numeric value. It is used inside the **output_field()** expression. If the string number does not have a standard base prefix, the method assumes it to be in a decimal representation.

***Syntax:***

<number> = to_int(<expr> [, base=0|2|10|16])  
<number> = to_uint(<expr> [, base=0|2|10|16)  
<number> = to_aint(<expr> [, base=0|2|10|16])

***Returns:*** Numeric value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| expr | UTDB Expression | the expression to change to numeric DataType |
| **base** | Number | for string expressions indicate the radix to use for parsing the string into a number |

***Notes:***
- On integer DataTypes, produces the same value with an option to change the value type to be signed/unsigned.
- On float DataType, produces a truncated value. (python-like semantics)
- On string datatype, produces an integer value by interpreting the operand expression as a number in a certain radix.
- Radix can be specified as <base> argument, or if <base> is 0 (default), it can be inferred from the first two characters of the string.
- If the first two characters are “0x”, the inferred radix is 16.
- If they are “0b”, the inferred radix is 2, otherwise, the inferred radix is 10.
- Digits in the interpreted string should be within the range of the radix used for interpretation, and can be either lowercase or uppercase; otherwise it is an error.
- The input string should not have any extra characters besides whitespace, otherwise the conversion fails.
 
***Code Example:***
``` py

# convert hexadecimal string to signed number
output_field('X14', to_int('+0XAbC'))
 
# convert binary string to unsigned number
output_field("X16", to_uint('0b101'))

```

### 3.5.3 to_bin method
The **to_bin()** method is used to convert a numeric value expression to a binary representation string. it Is used inside the **output_field()** expression. It has an option to add a base prefix to the number (0b/0B).

***Syntax:***

<bin_string> = to_bin((<int_expr>[, upper_case=True|False] [, base_prefix=True|False]

***Returns:*** binary formatted string

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| int_expr | Numeric expression | Numeric expression that will be converted to a binary string representation. |
| **upper_case** | Boolean | If True - will use upper case letters in the result string. If False - will use lower case letters in the result string. ***Default:*** **False** |
| **base_prefix** | Boolean | If True - will add base prefix to the results string. If False - will not add base prefix to the results string. ***Default:*** **False** |


***Notes:***

***Code Example:***
``` py

# convert number to binary string with base prefix and upper case letters
output_field('FIELD', to_bin(trace.all.COREREQID + 31, True, True))
 
# convert number to binary string with no base prefix and lower case letters
output_field("Y16", to_bin(1234567890))

```

### 3.5.4 to_hex method
The **to_hex()** method is used to convert a numeric value expression to a hexadecimal representation string. it Is used inside the **output_field()** expression. . It has an option to add a base prefix to the number (0x/0X).

***Syntax:***

<hex_string> = to_hex((<int_expr>[, upper_case=True|False] [, base_prefix=True|False]

***Returns:*** hexadecimal formatted string

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| int_expr | Numeric expression | Numeric expression that will be converted to a hexadecimal string representation. |
| **upper_case** | Boolean | If True - will use upper case letters in the result string. If False - will use lower case letters in the result string. ***Default:*** **False** |
| **base_prefix** | Boolean | If True - will add base prefix to the results string. If False - will not add base prefix to the results string. ***Default:*** **False** |

***Notes:***

***Code Example:***
``` py

# convert number to hexadecimal string with base prefix and lowercase letters
output_field('FIELD', to_hex(trace.all.COREREQID + 31, False, True))
 
# convert number to binary string with base prefix and uppercase letters
output_field("Y16", to_hex(-1, base_prefix=True, upper_case=True))

```

## 3.6 Hierarchical methods
Hierarchical expressions methods refer to hierarchical data structure (tree like) in UTDB. For that matter, records may have a single parent, and/or multiple children. In addition, a record can be a “root”, meaning it has no parent, or a “leaf”, meaning It has no children.

The hierarchical methods return boolean values and are used as part of the query filter (where) expression.

### 3.6.1 is_root method
The is_root method is used to find records that are tree root records. meaning records that have no parent.

***Syntax:***

<bool_expr> = is_root()

***Returns:*** Boolean Value

***Parameters:*** None

***Notes:***

***Code Example:***
``` py

# find root records with time bigger than 1000
query1 = from_(trace).where(is_root() & (tr.all.TIME > 1000))

```

### 3.6.2 root_of method
The **root_of()** method is used to filter tree root record which is a parent of some other selected child record.

***Syntax:***

<bool_expr> = root_of(where(<child_record_filter>)

***Returns:*** Boolean expression

***Parameters:*** 

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| child_record_filter | Boolean expression | Filter expression for finding the required parent record. |


***Code Example:***
``` py

# find roots for records with OPCODE 'Read'
query1 = from_(trace).where(root_of(where(trace.all.OPCODE == "Read")))

```

### 3.6.3 is_leaf method
The **is_leaf()** method is used to find records that are tree leaf records. meaning records that have no children.

***Syntax:***

<bool_expr> = is_leaf()

***Returns:*** Boolean value

***Parameters:*** None

***Notes:***

***Code Example:***
``` py

# find leaf records with time bigger than 1000
query1 = from_(trace).where(is_leaf() & (tr.all.TIME > 1000))

```

### 3.6.4 leaf_of method
The **leaf_of()** method is used to find record which is child of some other selected parent record.

***Syntax:***

<bool_expr> = leaf_of(where(<parent_record_filter>)

***Returns:*** Boolean value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| parent_record_filter | Boolean expression | Filter expression for finding the required leaf record. |

***Notes:***

***Code Example:***
``` py

# find leaves of parents with OPCODE 'Read'
query1 = from_(trace).where(leaf_of(where(trace.all.OPCODE == "Read")))

```

### 3.6.5 child_of method
The **child_of method()** is used to find records that are children of a specified parent record. In this case, children of all tree levels (descendants) under the selected record are counted.

The child_of method accepts the parent record filter as input, using the query Where method.

***Syntax:***

<bool_expr> = child_of ( where(<parent_record_filter>) [, inclusive=<True|False>])

***Returns:*** Boolean value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| parent_record_filter | Boolean expression | Filter expression for finding the required child record. |
| **inclusive** | Boolean | Determines whether to include the parent record in the results. ***Default:*** **True**|

***Notes:***

***Code Example:***
``` py

# find descendants of records with NAME equals to "top_flow"
query1 = from_(trace).where(child_of(where(trace.all.NAME == "top_flow")))

```

### 3.6.6 child_of_root method
The **child_of_root method()** is used to find records that are children of a specified parent record which is also a root record. In this case, children of all tree levels (descendants) under the selected record are counted.

The **child_of_root()** method accepts the parent record filter as input, using the query Where method.

The **child_of_root()** method carries the same result as using **child_of()** and **is_root()** together.

***Syntax:***

<bool_expr> = child_of_root ( where(<parent_record_filter>) [, inclusive=<True|False>])

***Returns:*** Boolean value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| parent_record_filter | Boolean expression | Filter expression for finding the required parent record. |
| **inclusive** | Boolean | Determines whether to include the parent record in the results. ***Default:*** **True**|

***Notes:***

***Code Example:***
``` py

# find descendants of records with NAME equals to "top_flow"
query1 = from_(trace).where(child_of_root(where(trace.all.NAME == "top_flow")))

```

### 3.6.7 parent_of method
The **parent_of()** method is used to find records that are parents of a specified child record. In this case all parent tree levels (ancestors) of the selected record are counted.

The **parent_of()** method accepts the child record filter as input, using the query where matched.

***Syntax:***

<bool_expr> = parent_of( where(<child_record_filter>) [, inclusive=<True|False>])

***Returns:*** Boolean value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| child_record_filter | Boolean expression | Filter expression for finding the required child record. |
| **inclusive** | Boolean | Determines whether to include the parent record in the results. ***Default:*** **True**|

***Notes:***

***Code Example:***
``` py

# find ancestors of records with VAL greater than 1
query1 = from_(trace).where(parent_of(where(trace.all.VAL > 1))

```

### 3.6.8 parent_or_child_of method
The **parent_or_child_of()** method is used to find records that are parents or children of a specified record. In this case all ancestors and descendants of the selected record are counted.

The **parent_or_child_of()** method accepts the child record filter as input, using the query where matched.

The **parent_or_child_of()** method carries the same result as using **parent_of()** | **child_of()** as filters

***Syntax:***

<bool_expr> = parent_or_child_of ( where(<child_record_filter>) [, inclusive=<True|False>])

***Returns:*** Boolean value

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| child_record_filter | Boolean expression | Filter expression for finding the required child record. |
| **inclusive** | Boolean | Determines whether to include the parent record in the results. ***Default:*** **True**|

***Notes:***

***Code Example:***
``` py

# find ancestors of records with VAL greater than 1
query1 = from_(trace).where(parent_or_child_of(where( (tr.cpurequest.OPCODE == 'Read') )))

```


------------------------------

# 4 UTDB Queries and Views
UTDB queries are used to specify the data that needs to be retrieved from the UTDB source for the validation task in hand.

The UTDB data source can be viewed as a table of records of different types where each record has a set of fields with values.

The UTDB Query construction API includes the following objects:

 - Query Object
 - View Object

## 4.1 Query Object
The Query object is a result of query construction. Query construction is done by calling query construction methods.
Query construction methods have two variants:

- Global variant - a global function that returns a new query object according to its semantics.
- Class member variant - a member method of a previously constructed Query object; returns a new query object that appends additional details to an existing query.

The full query construction can be done by chaining multiple calls in the form func1().func2().func3().

Query object has the following methods:

- **fields()** method
- **where()** method
- **from_()** method
- **sort_by()** method
- **limit()** method
- **first()** and **last()** methods
- **group_by()** method
- **having()** method
- Parametrized Queries:
    - **bindparam()** method
    - **bind()** method
- **partition_by()** method

### 4.1.1 fields method

The **fields()** method is used to specify the fields that will be retrieved the trace by the query. The method has a global variant and a UTDB Query member variant.

***Syntax:***

<query> = fields(<field_expression> [, <field_expression>,…])

<query> = <query>.fields (<field_expression> [, <field_expression>,…])

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| field_expression | value expression  | Field or OutputField|

***Notes:***
- Can be applied multiple times and the parameters will be accumulated.
- The order of the fields in the result will corelate to the order in which they were specified.

***Code Example:***
``` py

# select two fields to be obtained
query1 = fields(trace.all.FIELD1, trace.all.FIELD2)
 
# add another field to be obtained
query2 = query1.fields(trace.all.FIELD3)

```

### 4.1.2 where method
The **where()** method is used to specify a filter for the trace records in the query. The method has global variant and a UTDB Query member variant.

***Syntax:***

<query> = where(<boolean_expression>)

<query> = <query>.where(<boolean_expression>)

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| boolean_expression | Boolean Expression| UTDB Value Expressions |

***Notes:***
- Can be called multiple times and the conditions will be accumulated with a logical AND between them

***Code Example:***
``` py

# using global “where” method to create new query object with 1 filter
query1 = where(trace1.all.FIELD1 == 5)
 
# add another condition
query2 = query1.where(trace1.all.FIELD2 == "read")

```

### 4.1.3 from_ method
The **from_()** method is used to specify the source for the query. The method has a global variant and a UTDB Query member variant.

***Syntax:***

<query> = from_(<trace> | <query> | <view> [,  ignore_hierarchy = <True|False>  ])

<query> = <query>.from_(<trace> | <query> | <view> [,  ignore_hierarchy = <True|False> ])

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| trace | Trace | A trace that the data will be taken from |
| query | Query | Another query object, result of which will serve as input for the constructed query |
| view | View | View object, result of which will serve as input for the constructed query |
| **ignore_hierarchy** | Boolean | flag which controls the hierarchical source access to be hierarchical (considering the parent-child relationships) or flat. The ***Default:*** **False** |

***Notes:***

- If from_ is not called in the query, it is automatically inferred to be the Trace object that is used in other parts of the query definition.
- Can be specified only once per query object.

***Code Example:***
``` py

# source is a trace
query1 = from_(trace)
 
# source is another query
query2 = from_(where(trace.all.FIELD1 == 5))
 
# source in inferred to be from trace where specification
query3 = where(trace.all.FIELD1 == 5)

```

### 4.1.4 sort_by method
The **sort_by()** method is used to specify the order of the returned records.

***Syntax:***

<query> = sort_by((<value_expression>, <order>) [, …])

<query> = <query>.sort_by((<value_expression>, <order>) [, …])

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| value_expression | Value Expression | Expression that can be used to set order of results records. |
| order | [ASC | DESC] | The order of the sorted values. ***Default:*** ASC|

***Notes:***
- **sort_by()** method can accept multiple sort definitions and be applied multiple times.
- Sort definitions will be applied in the order of the definitions where the first parameter will determine the primary sort factor, the second will determine the secondary sort factor and so on.

***Code Example:***
``` py

# define primary and secondary order of data set
query1 = sort_by((trace.all.FIELD2, ASC), (trace.all.FIELD1 + 3, DESC))
 
# add another sort level
query2 = query1.sort_by((trace.all.FIELD3, DESC))

```

### 4.1.5 limit method
The **limit()** method is used to limit the number of the retrieved records. The method has global variant and a UTDB Query member variant.

***Syntax:***

<query> = limit(<amount> [,<offset>])

<query> = <query>.limit(<amount>[, <offset>])

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| amount | Number | A max amount of records to be retrieved. |
| offset | Number | Determines from which record number to start counting the amount of retrieved records. Optional. ***Default:*** 0 |

***Notes:***
- Can be specified only once per query object.
- The number of records retrieved will be the lowest among <amount> and the number of records till the end of the trace.

***Code Example:***
``` py

# limit retrieved records
query1 = from_(trace).limit(10)
 
# limit retrieved records starting from offset
query2 = limit(10, 5).from_(trace)

```

### 4.1.6 first/last method
The **first()** method is used to get a specified number of consecutive records from the beginning of the query results list. The **last()** methods is used to get a specified number of preceding records from the end of the query results list. The default order of the records is the order of data insertion (usually the same order as in the original input log).

***Syntax:***

<query> = <query>.first(<amount>)

<query> = <query>.last(<amount>)

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| amount | Number | A number of elements to get in the results. ***Default:*** 1|

***Notes:***
- Can be specified only once per query object

***Code Example:***
``` py

# get first 10 records from the trace
query1 = from_(trace).first(10)
 
# get the last record sorted by OPCODE
Query2 = sort_by((trace.all.OPCODE, ASC)).last()

```

#### 4.1.7 group_by method
The **group_by()** method is used to group results by values of specified fields. The method has a global variant and a UTDB Query member variant. The method accepts a list of field expression parameters and returns a list comprising - for each value - a single record detected based on these expressions. Multiple value expressions will create a results record for each set of found values.

***Syntax:***

<query> = group_by(<value_expression> [,<value_expression>])

<query> = <query>.group_by(<value_expression> [,<value_expression>])

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| value_expression | Value Expression | Expression that results in a value used by the query to group items with the same value. |

***Notes:***

***Code Example:***
``` py

# group by single value expression
query1 = group_by(trace.all.ADDRESS)
 
# group by multiple value expressions
query2 = group_by(trace.all.ADDRESS, trace.all.COREREQID)
 
# group by single output field expression
Query3 = group_by(output_field("COMPUTED", trace.all.COREREQID + 2))

```

### 4.1.8 having method
The **having()** method is used to filter group_by results by fields based on some Boolean expression. The method has a global variant and a UTDB Query member variant. The method accepts a UTDB boolean expression and the group_by results will be filtered based on this expression.

***Syntax:***

<query> = having(<boolean_expression>)

<query> = <query>.having(<boolean_expression>)

***Returns:*** Query object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| value_expression | Boolean Expression | Expression that will be used to filter group_by results in a value used by the query to group items with the same value. |

***Notes:***
- If having is used without a group_by expression, it is assumed that all the trace records represent a single group. In this case, the results will have a single record with field name RESULT and a value of 0 or 1 (based on the condition expression).

***Code Example:***
``` py

# group by with having filer
query1 = group_by(trace.all.ADDRESS)).having(trace.all.ADDRESS > 100)
 
# group by multiple value expression
query2 = having(trace.all.OPCODE != 'WRITE')

```

### 4.1.9 Parameterized Queries
A parameterized query is used to create several, sometimes many, queries with identical syntactic structure but differing from one another by certain values. To accomplish that, value placeholders can be used in a query construction. A value placeholder is an object constructed by a **bindparam()** function and later used anywhere a value expression can appear. Multiple placeholders can be used, or the same placeholder can be used multiple times within the same query construction.

A parameterized query can be concretized explicitly using the **bind()** function to produce a list of concrete queries given a mapping of placeholder keys to the actual values they should be substituted with.

***Note:***
- A parameterized query may be used in a definition of a Query Coverpoint (see section #7.3 Coverpoint object). In this case, value substitution is done using the **bin()** or **bin_per_value()** methods (see sections #7.3.1, 7.3.3).

***related methods and attributes:***
- **bindparam()** method
- **bind()** method

#### 4.1.9.1 bindparam method
The **bindparam()** method is used to construct a value placeholder.

***Syntax:***

<bindparam> = bindparam(<name_of_parameter>)

short version:

<bindparam> = P(<name_of_parameter>)

***Returns:*** Bindparam object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name_of_parameter | String | The name of the value placeholder. |

***Notes:***
- P() - a shorter alias for bindparam() for the sake of a shorter code.

#### 4.1.9.2 bind method
The **bind()** method is used to concretize a parameterized query given a mapping of placeholder keys to the actual values they should be substituted with.

***Syntax:***

<list_of_queries> = bind(<parameterized_query>, <parameters_values_mapping>)

***Returns:*** list of Query objects with substituted values of Bindparam objects

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| parameterized_query | Query object | A Query containing value placeholders (Bindparam objects). |
| parameters_values_mapping | Dictionary | Contains a mapping of Bindparam objects to the list of values they should be substituted with. |

***Code Example:***
``` py

opcodes = [“READ”, “WRITE”]
datalens = [8, 16, 32]
 
# create bindparam object for opcodes (using alias P)
opcode_param = P('opcode')
 
# create bindparam object for datalen
dl_param = bindparam('dl')
 
# connect to trace
trace = connect (...)
 
# event without parameter
c2u_req_e = (trace.all.REQTYPE == "C2U")
# event with 'opcode' parameter
opcode_e = (trace.all.OPCODE == opcode_param)
# query with parameterized expression
c2u_opcode_x_dl = where(c2u_req_e & opcode_e & (trace.all.DATALEN == dl_param))
 
# generate list of queries for all possible sets of <opcode,datalen> values:
# <"READ",8>, <"READ",16>,...<"WRITE,32>
q_list = bind(c2u_opcode_x_dl, {opcode_param: opcodes, dl_param: datalens} )

```

### 4.1.10 partition_by method
The **partition_by()** method is used to divide trace/input data into segments based on specific field values. The method has global variant and a UTDB Query member variant. When **partition_by()** is given, the query results are organized into a two-level hierarchy where the top level corresponds to the partition value and the second level contains the records that match this partition value(s)

***Syntax:***

<query> = partition_by(<field_expression> [,<field_expression>, ...])
<query> = <query>.partition_by(<field_expression> [,<field_expression>, ...])

***Returns:*** Query object

***Parameters:***

| Parameter Name   | Type             | Description |
| ---------------- | ---------------- | ----------- |
| field_expression | Field Expression | Expression that is a field from the trace or defined output field. |

***Notes:***
- When more than one field expression is specified, the key for the partition will be the combination of the specified fields’ values.
- The result of the query is two-level hierarchical data where record type of top level is **"utdb_match"**. The second-level records retain their original record types. If the original record type is anonymous, the records in the second level will be labeled as **"utdb_event"**.
- In case the source records type is anonymous, the records type will be "event"
- Query expression cannot include more than one **partition_by** call.
- Query expression cannot include both **partition_by** and **detect** methods calls.
- This feature is functional only for "pg*" backends (new storage)

***Code Example:***
``` py
all = trace.all
# partition by records OPCODE field value
query = from_(base_query).partition_by(all.OPCODE)

 
# partition by records OPCODE field and some output field value
id_field = output_field("ID", to_str(all.COREREQID))
query = from_(base_query).partition_by(all.OPCODE, id_field)

```
#### 4.1.10.1 partition_by results
**partition_by** result is an iterator of two-level tree where the top level represents the partition and its fields values, the next level includes all records that have matching fields values.

additional information:
- The order of the top partition records is the order of the first record in the query source that matches the partition fields values,
- The order of the records under the partition is based on their appearance in the query source
- The record type of the partition records is **utdb_match**
- The record type of the records under the partition is their original record type (if it exists)
- If the record type does not exist (anonymous) the **utdb_event** record type will be assigned.

***partition_by OPCODE Results Example:***

```

#header,all,COREREQID,OPCODE,TIME
#header,cpurequest,COREREQID,OPCODE,TIME
#header,nbrequest,COREREQID,OPCODE,TIME
#header,nbresponse,COREREQID,OPCODE,TIME
#header,sbresponse,OPCODE,TIME
#header,utdb_match,OPCODE
   | RECORD_TYPE | COREREQID | OPCODE | TIME
============================================
+  | utdb_match  |           | Read   |     
 - | cpurequest  |         0 | Read   | 1000
 - | cpurequest  |         3 | Read   | 1300
 - | nbrequest   |         3 | Read   | 1305
+  | utdb_match  |           | CmpD   |     
 - | nbresponse  |         0 | CmpD   | 1006
+  | utdb_match  |           | Write  |     
 - | cpurequest  |         1 | Write  | 1100
 - | nbrequest   |         1 | Write  | 1102
 - | cpurequest  |         2 | Write  | 1200
+  | utdb_match  |           | Cmp    |     
 - | sbresponse  |           | Cmp    | 1106
 - | nbresponse  |         1 | Cmp    | 1112
 - | nbresponse  |         2 | Cmp    | 1210

```


## 4.2 View Object
The View object represents the results of one or more queries' results (fields and data). The metadata describes all the information about the record types, the fields that reflect the parameter queries or other viewed results.

***View object related methods and attributes:***
- view - global method to create a new View based on a single query's results
- union_view - global method to create a new View based on multiple queries' results aggregation.
- metadata - similar to the Trace object's interface and functionality

### 4.2.1 view Method
The global method **view()** creates a new View object based on a single query's results.

***Syntax:***

<view> = view(<query> [, rename_record_types=<record_type_mapping>])

***Returns:*** View object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| query | Query object | Constructed query for using its defined results' data |
| **rename_record_types** | Dictionary | A dictionary mapping each record type to its new name |

***Notes:***

***Code Example:***
``` py

#connect to trace
trace = connect (...)
 
# define view1 with a subset of fields from trace and an additional field representing the name of the original tracker
view1 = view(fields(output_field("TRACKER", "trace"), trace.all.TIME, trace.all.OPCODE).where(trace.all.TIME > 3000))
  
# view1 will contain TRACKER, TIME, and OPCODE fields
# create a query on to of view1
query1 = where(view1.all.OPCODE.contains('Cmp')).limit(3,-5)
 
# define view2 with all trace fields and rename its record type 'cpurequest' to 'foo'
view2 = view(from_(trace), rename_record_types = {trace.cpurequest : 'foo'})
 
# create a query on top of view2
query2 = fields(view2.foo.OPCODE).where(view2.foo.ADDRESS > 10000)

```

### 4.2.2 union_view Method
The global method union_view creates a new View object based on the aggregation of multiple viewable items' (queries or views) results.

***Syntax:***

<view> = union_view(<viewable_items_list>[, sort_by=<list_of_sort_by_tuples>] [, ignore_hierarchy=[True|False]] )

***Returns:*** View object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| viewable_items_list | list of Queries or View objects | Constructed query for using its defined results' data |
| **sort_by** | list of tuples | A list of tuples where each tuple includes (<field_name>, <order>) where order can be [ASC | DESC]. ***Default:*** ASC|
| **ignore_hierarchy** | Boolean | Boolean flag which controls the hierarchical source access to be hierarchical (considering the parent-child relationships) or flat. ***Default:*** False |


***Notes:***
- union_view restrict using traces and products of traces arguments from the same UTDB format, For example, union_view does not support using logdb with pg, only from a single format

***Code Example:***
``` py

#connect to trace
trace = connect (...)
trace2 = connect (...)
 
# define queries on trace
q1 = fields(trace1.all.TIME), trace1.all.ADDRESS, trace1.all.DATA)
q2 = fields(trace2.all.TIME, trace2.all.ADDRESS, trace2.all.DATA)
 
# define view based on q2 + changing record_type
v2 = view(q2, rename_record_types = { trace2.all : 'pcode_ioreg' })
 
# define union view based on q1 and v2 and sort by time
view = union_view(q1,v2, sort_by=[('TIME', ASC)])
 
# define queries which returns hierarchical result
q3 = detect(..., output=HIERARCHICAL)
q4 = detect(..., output=HIERARCHICAL)
 
# define union view based on q3 and q4 and sort by time
# pay attention, sorting is available for flat data only
view = union_view(q3,q4, sort_by=[('TIME', ASC)], ignore_hierarchy=True)

``` 


-----------------------------------

# 5 UTDB Data Retrieval
UTDB Data retrieval includes multiple methods. The retrieved data can be accessed or sorted using the following methods:

fetch method retrieves data and returns an iterable Results object for python script access.
fetch_count processes the data and returns the number of records in the related results.
dump method retrieves data and prints it in a human readable format to the screen or to a file.
store method retrieves data and stores it in a non human readable format (e.g. UTDB database) for further usage.

## 5.1 Data Retrieval global methods

### 5.1.1 fetch Method
The global method **fetch()** invokes query execution and returns query results.

***Syntax:***

<results> = fetch(<query>)

***Returns:*** Results object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| query | Query object | Constructed query that needs to be executed |

***Notes:***

***Code Example:***
``` py

# construct a query
query = from(trace).limit(10)
 
# execute the query and get results
results = fetch(query)

```

### 5.1.2 fetch_count Method
The global method **fetch_count()** invokes query execution and returns the number of records found.

***Syntax:***

<num_results> = fetch_count(<query>)

***Returns:*** Number

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| query | Query object | Constructed query that needs to be executed |

***Notes:***

***Code Example:***
``` py

# construct a query
query = from(trace).limit(10)
 
# execute the query and get number of found records
num_results = fetch_count(query)

```

### 5.1.3 dump Method
The global method **dump()** prints the results of a query to stdout or to a file in psv format.

***Syntax:***

dump(<query>, output=<path>, output_format=<format>, hide_metadata=<True|False>, formatting_dictionary=<fields_format_dict>, condensed_format=<True|False>, page_size=<lines_per_page>, hierarchical=<True/False>, vertical_headers=<True/False>, ignore_display_name=<True|False>)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| query | Query object | A query to print its results. |
| **output** | String | File or a directory based on the output_format. ***Default:*** stdout |
| **output_format** | String | Format can be one of: 'psv' (pipe separated value - pretty table), 'csv' (comma separated value). ***Default:*** 'psv' |
| **hide_metadata** | Boolean | Print record-type as a column and header of record type or not. Record type all header is always printed. If there is exactly one nameless record-type, then record-type is never printed even if hide_metadata is set to false. ***Default:*** **False**|
| **formatting_dictionary** | String to string dictionary | Dictionary to define the printing format of fields. The key, given a as string, is a field name. The value is a format string in python syntax. |
| **condensed_format** | Boolean | If True, will print in condensed (overlapping) mode (as in old Venus GUI). If False, will print in spreadsheet mode (as in new UTDB GUI). ***Default:*** **False** |
| **page_size** | Number | Print the title every page_size rows. Zero for printing the title once at the beginning. WARNING: it can cause to out of memory error when having a lot of rows. ***Default:*** 100 |
| **hierarchical** | Boolean | (When output format is PSV) Print additional columns to the left of the table visualizing a tree structure of records. Leaves in the tree are marked with '-' character, and internal nodes (including tree roots) with '+' character. Character is indented according to the record's depth in the tree. ***Default:*** **False** |
| **vertical_headers** | Boolean | (When output format is PSV) print headers vertically based on the width of data in the column. ***Default:*** **False** |
| **ignore_display_name** | Boolean | If True, ignores the display names defined for fields and uses their actual names instead. ***Default:*** **False** |

***Notes:***
- octal format is not supported

***Code Example:***
``` py

trace = connect("mydb")
query = from_(trace)
 
# print to stdout in psv format
dump(query)
 
# print to "out.txt" file in psv format
dump(query, output = "out.txt", output_format="psv")
 
# print stdout in psv format where ADDRESS integer field is printed as a hexadecimal
dump(query, formatting_dictionary = {"ADDRESS": "{:#x}"})
 
# print to stdout in psv format as a spreadsheet
dump(query, condensed_format = False)

```

### 5.1.4 store Method
The global method **store()** stores view data or query results to UTDB.

***Syntax:***

store(<query> | <view>, connection_string=<[storage_type:]destination_path>)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| query | Query object | Runs the query and stores its results. |
| view | View object | Gets view data and stores it. |
| connection_string | String | A string that describes [UTDB storage type](#167-utdb-storage-types) and destination path. |


***Notes:***

***Code Example:***
``` py

trace = connect("mydb")
q1= from_(trace)
 
# store query to utdb_files/query_utdb
q1_utdb_location = utdb_files/query_utdb
store(q1, q1_utdb_location)
 
# store query to utdb_files/view_utdb
v1_utdb_location = utdb_files/view_utdb
store(v1, v1_utdb_location)

```

## 5.2 Results Object
Results object is an iterable python object, that contains records of query results. During the iteration, each item represents one record of the results. The fields are obtained in the form of a python named tuple, i.e. the name (Field name) is assigned to each member, as well as the numeric index.

The results' records content depends on the query. It can be a subset of fields, group_by results or other records.

An individual item may contain the subset of the original record fields based on the fields that were requested by the query.

***Code Example:***
``` py

# execute simple inline query, selecting subset of the fields
results = fetch(fields(trace.all.RECORD_TYPE, trace.all.TIME, trace.all.COREREQID))
 
# simple reading of results records using python iterator
for res in results:
    print(res)
    # use specific record field name for specific check
    if res.RECORD_TYPE == 'CPURequest':
    # use record field index for printing
        print('found request', res[0], 'at time', str(res[1]))
 
#output example
(RECORD_TYPE = 'CPURequest', TIME = 1000, COREREQID = 0)
found request CPURequest at time 1000
(RECORD_TYPE = 'NBResponse', TIME = 1006, COREREQID = 0)
(RECORD_TYPE = 'CPURequest', TIME = 1100, COREREQID = 1)
found request CPURequest at time 1100
(RECORD_TYPE = 'NBResponse', TIME = 1112, COREREQID = 1)
(RECORD_TYPE = 'CPURequest', TIME = 1200, COREREQID = 2)
found request CPURequest at time 1200
(RECORD_TYPE = 'NBResponse', TIME = 1210, COREREQID = 2)

```

------------------------------

# 6 UTDB Flow Detection
UTDB flow detection API is used to search for and detect system level flows. System flows are represented by multiple events happening in the system during a period of time. An example for that can be a request event followed by a response event, or a read event followed by a completion event.

In UTDB, system events are represented by data records in UTDB trace, which was uploaded from some test execution output collateral (e.g. log file). These records are found using a user condition (boolean) expression that is checked against each record and returns True if the expression matches the record data.

***Flow detection API includes the following elements:***
- Event - represents a system event (corresponds to some record in UTDB Trace)
- Flow - an object that represents a system flow in terms of events and their time and data relationship
- Flow **abort** parameter
- Flow elements repetitions - for specifying some flow element multiple times in the flow
- Flow Variables - variable that can be set and used as part of the flow to define data dependencies between events in the flow and other usages
- **detect()** method - used to create a query from a flow and provide additional flow detection parameters
- Flow Detection results

***Flow Detection related objects and methods:***
- Event object
- Lookahead object
- eot (end of trace) expression
- Flow object
- Flow Variables
- Flow Detection Query
- Flow Detection Results
- Flow Detection Semantics

## 6.1 Event object
Event object represents a record in the UTDB trace in terms of condition expression on its data. Event object contains a Boolean expression and can have a name given by the user. Event objects can be a parameter of flow construction methods specifying the relationships between flow elements.

***Event object related methods and attributes:***
- **event()** - global method to create new event
- **name** - attribute name of the event object

### 6.1.1 event method
The **event()** method is called by the user to create a new event object.
It accepts the following values:
- A Boolean expression that is tested against a trace record to find a match
- A name for identifying this event in the results
- **assign** and **test_or_set** dictionaries to handle flow variables.
- See more information in Flow Variables section.

***Syntax:***

<event> = event(<condition> [name=<event_name>] [,assign=<var_value_pairs>] [,test_or_set=<var_value_pairs>])

***Returns:*** Event object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| condition | Boolean expression | The condition is checked against the trace records. If True, the record is considered to represent this event in the trace. |
| **name** | String | A name for the event. ***Default:*** empty string |
| **assign** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, sets the value to the related evaluated value expressions in the dictionary (see Flow Variables below). ***Default:*** **None** |
| **test_or_set** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, If Flow Variable is not set - does the same as the assign parameter. Otherwise, compares the Flow Variables value to the value expression and considers the result to be part of the Event detection condition. ***Default:*** **None** |

***Notes:***

***Code Example:***
``` py
# simple event creation where time is 200
e1 = event(trace.all.TIME == 200)
 
# event creation where time is longer than 200 with name
e2 = event(trace.all.TIME > 200, name='late_event')

```

### 6.1.2 name attribute
**name** attribute is a read-only attribute of an Event object. It returns the name that was set by the user for the Event object.

***Syntax:***

<event_name> = <event>.name

***Returns:*** String name of the event

***Code Example:***
``` py

# event creation where time bigger than 200 with name
e1 = event(trace.all.TIME > 200, name='late_event')
 
# get event name
e1_name = e1.name

```

## 6.2 Lookahead object
Lookahead object represents a point between records in a UTDB trace. The Lookahead object contains a Boolean expression that is evaluated with the record immediately following the point between records, and can have a name given by the user. Lookahead objects can be a parameter to flow construction methods specifying the relationships between flow elements.

***Lookahead object related methods and attributes:***
- **lookahead()** - global method to create new lookahead
- **name** - attribute name of the lookahead object

### 6.2.1 lookahead method
The **lookahead()** method is called by the user to create a new Lookahead object. It accepts:
- A Boolean expression that is tested against a trace record to find the point between records preceding a record that satisfies the expression.
- Name for identifying this Lookahead in the results.
- assign and test_or_set dictionaries to handle flow variables. See more information in the Flow Variables section.

***Syntax:***

<lookahead> = lookahead(<condition> [name=<lookahead_name>] [,test_or_set=<var_value_pairs>] [,assign=<var_value_pairs>])

***Returns:*** Lookahead object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| condition | Boolean expression | The condition is checked against the trace records and if True the lookahead is satisfied at a point immediately preceding that record. |
| **name** | String | A name for the lookahead. ***Default:*** empty string |
| **assign** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, sets the value to the related evaluated value expressions in the dictionary (see Flow Variables below). ***Default:*** **None** |
| **test_or_set** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, If Flow Variable is not set - does the same as the assign parameter. Otherwise, compares the Flow Variables value to the value expression and considers the result to be part of the Lookahead detection condition. ***Default:*** **None** |

***Notes:***

***Code Example:***
``` py

# simple lookahead creation where time is 200
la1 = lookahead(trace.all.TIME == 200)
 
# lookahead creation where time bigger than 200 with name
e2 = lookahead(trace.all.TIME > 200, name='late')

```

### 6.2.2 name attribute
**name** is a read-only attribute of the Lookahead object. It returns the name that was set by the user for the lookahead object.

***Syntax:***

<lookahead_name> = <lookahead>.name

***Returns:*** String name of the Lookahead

***Code Example:***
``` py
# lookahead creation where time bigger than 200 with name
la_1 = lookahead(trace.all.TIME > 200, name='late')
 
# get lookahead name
la_1_name = la_1.name

```

## 6.3 eot method
The **eot()** method creates an expression that represents the end of the trace. This expression is useful, for example, when using an unbounded loop at the end of sequences. By default flow detection will report a flow as complete as soon as possible, without waiting for additional events that can be matched past that point. Adding **eot()** as the last event in the sequence will cause the algorithm to collect all repetitions until the end of the trace.

***Syntax:***

<lookahead> = eot()

***Returns:*** end of trace event

***Parameters:*** None

***Notes:***
- Using eot can drastically impact the performance and memory consumption of the flow detection process. Whenever possible use eot in an OR condition or in one_of() where you can define an alternative condition that signifies the proper end of a flow before the end of the trace.

***Code Example:***
``` py

# get multiple completion records for a request based on the request id
req_event = event(trace.all.OPCODE == 'Req', assign={var("req_id"):trace.all.REQID})
cmp_event = event((trace.all.OPCODE == 'Cmp') & var("req_id") == trace.all.REQID)
  
flow = seq( req_event, cmp_event['+'], eot())

```

## 6.4 Flow object
Flow object contains the expected order of the Events and Lookaheads related to the flow. Flow object is created by calling one of the flow construction methods which define specific ordering between flow elements.

Flow elements can be other flows (which are sometimes called sub-flows), event objects or condition expressions (Boolean expressions) used to find specific records in a trace, and lookahead objects used to assert a record existing in the trace.

In addition to the flow elements, the Flow construction method accepts the abort parameter. See more information in the Flow abort parameter section.

***The following methods are used to create a flow object:***
- **seq()** - method to create a flow with sequential order of its elements in the trace
- **all_of()** - method to create a flow where all its elements should happen concurrently (in the same period of time) which also means that their sub elements may occur in interleave between each other in the trace.
- **one_of()** - method to create a flow where only one of the sub elements may occur in the trace
- **repeat()** - method to create a flow where an operand may occur multiple times with an optional until condition

### 6.4.1 seq method
**seq()** method creates a new flow object. It accepts a list of flow elements and defines the expected sequential occurrence of the flows in the trace. This means that any flow element is expected to start after the records from the previous flow element were detected in the trace.

***Syntax:***

<flow> = seq(<flow_element_list> [,name=<flow_name>] [,abort=[Event | Boolean exp]] [,assign=<var_value_pairs>])

<flow_element_list> => <flow_element> [,<flow_element>,…]

<flow_element> => [Flow | Event | Boolean exp | Lookahead]

***Returns:*** Flow object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| **name** | String | Optional user given name for the flow |
| **abort** | Event or Boolean Expression | see Flow abort parameter section |
| **assign** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, sets the value to the related evaluated value expressions in the dictionary (see Flow Variables below). ***Default:*** **None** |

***Notes:***

***Code Example:***
``` py

# sequential flow using boolean expressions
f1 = seq(trace.all.OPCODE == 'Write', trace.all.OPCODE == 'Read')
 
# sequential flow using event object and boolean expression
f2 = seq(event(trace.all.OPCODE == 'Write'), trace.all.OPCODE == 'Read')
 
# sequential flow using:
# - predefined read python variable event object with name
# - write boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
f3 = seq(trace.all.OPCODE == 'Write', read)
 
# sequential flow using:
# - predefined read python variable event object with name
# - predefined write python variable boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
write = trace.all.OPCODE == 'Write'
write_read_seq = seq(write, read)
 
# sequential flow including a name using:
# - predefined read_write python variable flow object (above)
# - predefined check python variable event object
check = trace.all.OPCODE == 'Check'
write_read_check_seq = seq(write_read_seq, check, name='write_read_check)

```

***Flow Diagrams:***

![a](./assets/write_read_seq.png)


### 6.4.2 all_of method
**all_of()** method creates new Flow object. It accepts a list of flow elements and defines expected concurrent occurrence of the flow elements flows in the trace. This means that the flow elements do not have any particular order between them and can occur in any order in the trace.

***Syntax:***

<flow> = all_of(<flow_element_list> [,name=<flow_name>] [,abort=[Event | Boolean exp]] [,assign=<var_value_pairs>] )

<flow_element_list> = <flow_element> [,<flow_element>,…]

<flow_element> = [Flow | Event | Boolean exp | Lookahead]

***Returns:*** Flow object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| **name** | String | Optional user given name for the flow |
| **abort** | Event or Boolean Expression | see Flow abort parameter section |
| **assign** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, sets the value to the related evaluated value expressions in the dictionary (see Flow Variables below). ***Default:*** **None** |

***Notes:***

***Code Example:***
``` py
# concurrent flow using boolean expressions
f1 = all_of(trace.all.OPCODE == 'Write', trace.all.OPCODE == 'Read')
 
# concurrent flow using event object and boolean expression
f2 = all_of(event(trace.all.OPCODE == 'Write'), trace.all.OPCODE == 'Read')
 
# concurrent flow using:
# - predefined read python variable event object
# - write boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
f3 = all_of(read, trace.all.OPCODE == 'Write')
 
# concurrent flow using:
# - predefined read python variable event object
# - predefined write python variable boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
write = trace.all.OPCODE == 'Write'
read_write_all = all_of(read, write)
 
# concurrent flow including a name using:
# - predefined read_write python variable flow object (above)
# - predefined check python variable event object
check = trace.all.OPCODE == 'Check'
read_write_check_all = all_of(read_write_all, check, name='write_read_check)

```

***Flow Diagrams:***

![a](./assets/write_read_all_of.png)

### 6.4.3 one_of method
**one_of()** method creates a new flow object. It accepts a list of flow elements and defines that only one of flow elements should occur in the trace.

***Syntax:***

<flow> = one_of(<flow_element_list> [,name=<flow_name>] [,abort=[event | Boolean exp] [,assign=<var_value_pairs>])

<flow_element_list> = <flow_element> [,<flow_element>,…]

<flow_element> = [Flow | Event | Boolean exp | Lookahead]

 
***Returns:*** Flow object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| **name** | String | Optional user given name for the flow |
| **abort** | Event or Boolean Expression | see Flow abort parameter section |
| **assign** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, sets the value to the related evaluated value expressions in the dictionary (see Flow Variables below). ***Default:*** **None** |

***Code Example:***
``` py 
# concurrent flow using boolean expressions
f1 = one_of(trace.all.OPCODE == 'Write', trace.all.OPCODE == 'Read')
 
# concurrent flow using event object and boolean expression
f2 = one_of(event(trace.all.OPCODE == 'Write'), trace.all.OPCODE == 'Read')
 
# concurrent flow using:
# - predefined read python variable event object
# - write boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
f3 = one_of(read, trace.all.OPCODE == 'Write')
 
# concurrent flow using:
# - predefined read python variable event object
# - predefined write python variable boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
write = trace.all.OPCODE == 'Write'
read_write = one_of(read, write)
 
# concurrent flow including a name using:
# - predefined read_write python variable flow object (above)
# - predefined check python variable event object
check = trace.all.OPCODE == 'Check'
read_write_check = one_of(read_write, check, name='write_read_check)

```

***Flow Diagrams:***

![a](./assets/write_read_one_of.png)


### 6.4.4 repeat method
repeat() method creates new flow object. It accepts a flow element that is expected to be repeated, optional boundaries of repetition, and an until condition.

The until condition will be checked after every repetition of the flow. If the until condition is met, the following flow will be looked for. If the until condition is not met, a new repetition may start.

Until condition will be treated as Lookahead.

***Syntax:***

<flow> = repeat(<flow_element> [,name=<flow_name>] [,abort=[event | Boolean exp] [,assign=<var_value_pairs>] [,min=<integer constant>] [,max=<integer constant>] [,until=<Boolean exp>])

<flow_element> = [Flow | Event | Boolean exp]

***Returns:*** Flow object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| **name** | String | Optional user given name for the flow |
| **abort** | Event or Boolean Expression | see Flow abort parameter section |
| **assign** | Dictionary of Flow Variables and ValueExpressions | For each Flow Variable in the dictionary, sets the value to the related evaluated value expressions in the dictionary (see Flow Variables below). ***Default:*** **None** |
| min | Non Negative Number | Minimum number of repeats |
| max | Non Negative Number | Maximum number of repeats (inclusive) |
| until | Boolean Expression | Optional condition to stop the repetition - treated as Lookahead |

***Code Example:***
``` py

# collect all reads until write happens
f1 = repeat(trace.all.OPCODE == 'Read', until=trace.all.OPCODE == 'Write')

```

### 6.4.5 Flow elements repetitions
Flow elements repetitions is used to define multiple occurrences of some element in the flow. This can be specific a number of occurrences or some range definition.

Flow elements repetitions is defined using the slicing operator **[]**.

***Syntax:***

<flow_element>[<repetition_expr>]

The following table describes the supported repetition_expr values:

| Expression | Description |
| ---------- | ----------- |
| [x] | Exactly x repetitions |
| [x:y] | Between x and y repetitions |
| [x:] | Between x and any number of times |
| [:y] | Between 0 and y times |
| ['*'] | Between 0 to any number of times |
| ['+'] | Between 1 to any number of times [1:] |
| ['?'] | 0 or one times [:1] |

***Notes:***

***Code Example:***
``` py

e1 = event()
e2 = event()
e3 = event()
e4 = event()
 
# flow that detects sequential order of elements include repetitions
flow = seq(e1, e2[2:2], e3[:3], e4)

```

***Flow Diagrams:***

![a](./assets/elements_repetitions.png)


### 6.4.6 Flow abort parameter
The abort parameter is an event or a Boolean expression that is checked in addition to other flow elements, and if it matches a record, the flow is flow detection process is aborted and the flow is ignored.

***Syntax:***

<flow_method>(<flow_elements_list>, abort=<event | bool_expr>)

***Notes:***

***Code Example:***
``` py

# create sequential flow using boolean expressions abort boolean expressions
# the flow events are read=>write=>check
# the flow abort event is Ignore OPCODE
write = trace.all.OPCODE == 'Write'
read = trace.all.OPCODE == 'Read'
check = trace.all.OPCODE == 'Check'
ignore = trace.all.OPCODE == 'Ignore'
 
f1 = seq(write, read, check, abort=ignore)

```

***Flow Diagrams:***

![a](./assets/optional_occurrences.png)

## 6.5 Flow Variables
Flow variables are variables that can be set or used as part of the flow definition, to enable definition of data correlations between events in the flow or for other usages.

Flow Variables are used as part of the Event definition using the **test_or_set** or **assign** parameters. They are set when an Event record is detected by some record field value or by any other expression. After being set, they are used as part of an Event condition (Boolean expression).

Flow Variables can be used directly as part of the Event definition or be assigned to a python variable, where the python variable can be used as the Flow Variable in the event definition.

### 6.5.1 var object constructor
Flow variable is created by using the var() constructor method with a name parameter which uniquely identifies it in the flow.

***Syntax:***

<var> = var(<var_id>)

<event> = event(<condition>, assign=dict(<var(var_id)>:<expr>, ...), test_or_set=dict(var(var_id)>:<expr>, ...))

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| var_id | string | A unique name of this variable in the flow |

***Notes:***
- Event **assign** parameter behavior:
    - The variable is assigned with the value evaluated from the expression immediately after matching the event.
- Event **test_or_set** parameter behavior:
    - If the variable value is not set (i.e. the value is NULL) the behavior is the same as the assign parameter.
    - If the variable value is set (i.e. not NULL), the variable value is compared with the given expression and the result is combined with the event condition expression as part of the record matching process.
    - If the given expression evaluates to NULL, the variable will remain unset.
- A Flow variable can be used directly in the **test_or_set** or **assign** dictionary, or be defined as a python object and used in the dictionary or in the event condition expression.

***Code Example:***
``` py

# event creation using test or set 'coreid' flow variable
e3 = event(…, test_or_set={ var('coreid'): trace.all.COREID })
 
# event creation using test or set 'cpureq' flow variable as python object
cpureq = var('cpureq')
e4 = event(…, test_or_set={ cpureq: trace.all.CPUREQID} )
 
# using python 'cpureq' flow variable in event condition expression
e5 = event(trace.all.CPUREQID == cpureq)

```

## 6.6 Flow Detection Query

### 6.6.1 detect method
The **detect()** method is related to the query construction methods (global, or from another query), but is used only for creating a Flow Detection Query.

The **detect()** method accepts a Flow object and additional parameters related to the detection process output and detection algorithm rules.

<query> = <query>.detect(<flow>, output=<output_params>, mode=<mode_params>, measures=<measures>, partition_by=<expression>, unmatched_filter=<expression>)


***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| flow | Flow object | A Flow object created by Flow construction methods |
| **output** | Set of output flags | [see detect output flags definition](#-detect-output-flags) |
| **mode** | Set of mode flags | [see detect mode flags definition](#-detect-mode-flags) |
| **measures** | List of Measure objects | Measure objects created with **measure()** construction method (see measure details below) |
| **partition_by** | Field Expression or List of Field Expressions | expression to improve performance in cases the data can be partitioned in a way that flows exists in single partitioned value |
| **unmatched_filter** | Boolean Expression | UTDB expression to select only interesting **UNMATCHED** records for output; is applicable when **UNMATCHED** output flag is ON. ***Default:*** **True** |


***Code Example:***
``` py

flow = seq(trace.all.TIME < 1100, trace.all.TIME > 1100)
 
# sequential flow using boolean expressions
q1 = detect(flow, mode=NO_OVERLAPPING_MATCHES | ON_OVERLAP_DISCARD_OLD,  output=COMPLETE_MATCHES | INCOMPLETE_MATCHES)
 
 
f1 = seq(trace.all.OPCODE == 'Write', trace.all.OPCODE == 'Read')
 
# sequential flow using event object and boolean expression
f2 = seq(event(trace.all.OPCODE == 'Write'), trace.all.OPCODE == 'Read')
 
# sequential flow using:
# - predefined read python variable event object with name
# - write boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
f3 = seq(trace.all.OPCODE == 'Write', read)
 
# sequential flow using:
# - predefined read python variable event object with name
# - predefined write python variable boolean expression
read = event(trace.all.OPCODE == 'Read', name='Read')
write = trace.all.OPCODE == 'Write'
write_read_seq = seq(write, read)

```

#### detect output flags

| Flag             | Description |
| ---------------- | ----------- |
| COMPLETE_MATCHES | include complete occurrences in the output (default) |
| INCOMPLETE_MATCHES | include incomplete occurrences in the output |
| EXPECTED         | in incomplete occurrences, include all next possible Events/Lookaheads ('expected' records) that could have been progressed the Flow |
| UNMATCHED        | include unmatched records in the output ('unmatched' record is any record from input which does not belong to result with complete/incomplete status) |
| LOOKAHEADS       | include records evaluated for lookaheads in both, complete and incomplete occurrences |
| HIERARCHICAL     | will return iterator with full hierarchical structure of the flow constructs |
| TWO_LEVEL        | will return iterator with a 2 level flow detection structure, where Top level will be the occurrence top level flow construct record and next level will be the records of the matched events |
| DEFAULT_MEASURES | add UTDB_MATCH_NAME, UTDB_MATCH_STATUS and UTDB_MATCH_FLOW_TYPE measures and columns to the results records |

#### detect mode flags

| Primary Flag                  | Secondary Flag | Description |
| ----------------------------- | -------------- | ----------- |
| OVERLAPPING_MATCHES (default) | EXTEND_EARLIEST_FIRST (default) | Assume overlapping occurrences where first occurrence will consume first following events in the flow. |
| OVERLAPPING_MATCHES (default) | EXTEND_LATEST_FIRST | Assume overlapping occurrences where last occurrence will consume first following events in the flow. |
| NO_OVERLAPPING_MATCHES        | ON_OVERLAP_DISCARD_NEW | Assume no overlapping occurrences and discard start of new occurrences in the flow. |
| NO_OVERLAPPING_MATCHES        | ON_OVERLAP_DISCARD_OLD | Assume no overlapping occurrences and discard existing occurrence if new occurrences starts in the flow. |

### 6.6.2 Detect Measure object
Flow detection measures is a list of Measure objects. Measure object define additional computed field to the the Detect query results. Flow measures are defined by expressions that can be evaluated to a literal value. In addition, the displayed field format can be controlled (as in the schema field method).
For example, a Measure can be used to expose the value of a Flow Variable at the time of matching each row in results.

***Syntax:***

<measure> = measure(<measure_name>, <expression>  [, format=<format_string>] [, display_name=<string>])

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| measure_name | String | A unique name of this measure in the Detect query. Must be different from all other field references used in the query. |
| expression | Value Expression | UTDB expression that can be evaluated to a literal value. Can consist of literals, field-references, flow variables, built-in measure methods etc. |
| **format** | String | python style formatting string (e.g. '{:#x}'). Used to generate formatted string representation of the field value in **dump()** API and UTDB GUI. |
| **display_name** | string | A unique name to use as header name in **dump()** API |

***Notes:***

### 6.6.3 Built-in measures
Built-in Measure functions extract a value from the matched row in the flow detection results, that cannot be otherwise accessed with a UTDB expression.

The information is only relevant after a row is matched, thus these can only be used as measures, and not in a condition.

- **match_name()** - Evaluates to the name of the event/flow matched for the row.
- **match_status()** - Evaluates to completion status (COMPLETE/INCOMPLETE) of the matched flow.
- **match_flow_type()** - evaluated to flow type used (seq, one_of, all_of, repeat) and event type (event or lookahead)

***Code Example:***
``` py

# event assigns value to a flow variable
e1 = event(…, assign={ var('counter'): 1 }, name='starter')
e2 = event(…, assign={ var('counter'): var('counter') + 1 }, name='loop')
 
# flow using variables
f1 = seq(e1, seq(e2)['+'], name='flow_1')
 
# Measure exposes variable value
m1 = measure('M_COUNTER', var('counter'))
 
# Measure exposes calculation on fields
m2 = measure('M_SUM', trace.all.FIELD1 + trace.all.FIELD2, format='{:012x}')
 
# Measure exposes name of matched element
m3 = measure('M_NAME', match_name())
 
# Define detect query using above measures
query = detect(f1, measures=[m1, m2, m3])

```

### 6.6.4 DEFAULT_MEASURES flag
**DEFAULT_MEASURES** are three built in measures added to detect query output
- **match_name()** with measure name "UTDB_MATCH_NAME"
- **match_status()** with measure name "UTDB_MATCH_STATUS"
- **match_flow_type()** with measure name "UTDB_MATCH_FLOW_TYPE"

***Code Example:***
``` py

flow = seq(...)
q1 = detect(flow, output=DEFAULT_MEASURES)
Note: This is equivalent to defining each built-in measure with this name explicitly (using measure argument)
```

6.6.5 partition_by

Partitioning is a method used to describe disjoint sets of records that can only be correlated within a set. For example, in many cases, a unique or semi-unique transaction identifier exists. In such cases, partitioning can easily help describe this fact. 
The **partition_by** option accepts field expressions that can be evaluated using a record. When more than one expression is specified, the key for the partition will be the combination of the specified expressions' values. **partition_by** is equivalent to adding **test_or_set** in terms of results with variables for every event in the sequence, but it usually results in better performance.

``` py

f1 = seq(e1, e2)
 
# Events in each occurrence in the result will have same TID
query = detect(f1, partition_by=trace.all.TID)

# Events in each occurrence in the result will have same TID and ADDRESS
query = detect(f1, partition_by=[trace.all.TID, trace.all.ADDRESS])

```

## 6.7 Flow detection results
Flow detection results are retrieved by calling **fetch()** with the Detect query.

The returned Results of the Detect query are built out of top-level flow occurrences records. The flow occurrences record has build-in fields such as **RECORD_TYPE**, which will be equal to "utdb_match" and **UTDB_CHILDREN** which return a list of event records detected for the flow occurrence as well as special records with **utdb_expected** record type representing the next expected events in an incomplete flow occurrence. The expected records have no fields from the original schema, but will have all measure fields as defined in the section Detect Measure parameter.

If **UNMATCHED** output flag is ON, unmatched records are included into flow detection results.  Each unmatched record is reported as separate flow occurrence. The "unmatched" records have all fields from original schema including original record type of the record and default measure fields are equal to "unmatched", but user-defined measure fields are not calculated for them.  In the results, "unmatched" record appears in the vicinity of a complete/incomplete match it could have been related to, i.e. when current occurrence is reported, "unmatched" records detected from start-time of this occurrence until start-time of next occurrence (or END-OF-TRACE) are reported; "unmatched" records detected from START-OF-TRACE until start-time of first occurrence are reported before occurrence.

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
 
# print results example
utdb_match:
(TIME=1234, OPCODE='WRITE', ...)
 
# flow query reported with "unmatched" records
e1 = event(trace.all.OPCODE == 'Read', name='e1')
e2 = event(trace.all.OPCODE == 'Write', name='e2')
s1 = seq(e1, e2, name='s1')
 
q = from_(fields(trace.all.TIME, trace.all.OPCODE)).detect(s1, output=COMPLETE_MATCHES|INCOMPLETE_MATCHES|UNMATCHED|DEFAULT_MEASURES, unmatched_filter=(trace.all.OPCODE == "CmpD"))
 
for rec in fetch(q):
    print(rec[:])
    if hasattr(rec, "UTDB_CHILDREN"):
        for e in rec.UTDB_CHILDREN:
            print(e)
 
# results
('nbresponse', 200, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')
('nbresponse', 300, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')
 ('utdb_match', 'COMPLETE', 's1', 'seq')
---- ('cpurequest', 1000, 'Read', 'MATCHED', 'e1', 'event')
---- ('cpurequest', 1100, 'Write', 'MATCHED', 'e2', 'event')
 ('nbresponse', 1006, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')
 ('utdb_match', 'COMPLETE', 's1', 'seq')
---- ('cpurequest', 1300, 'Read', 'MATCHED', 'e1', 'event')
---- ('cpurequest', 1400, 'Write', 'MATCHED', 'e2', 'event')
 ('utdb_match', 'COMPLETE', 's1', 'seq')
---- ('nbrequest', 1305, 'Read', 'MATCHED', 'e1', 'event')
---- ('cpurequest', 1600, 'Write', 'MATCHED', 'e2', 'event')
 ('sbresponse', 1315, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')
 ('nbresponse', 1317, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')
('utdb_match', 'INCOMPLETE', 's1', 'seq')
---- ('cpurequest', 3200, 'Read', 'MATCHED', 'e1', 'event')
 ('utdb_match', 'INCOMPLETE', 's1', 'seq')
---- ('nbrequest', 3204, 'Read', 'MATCHED', 'e1', 'event')
 ('sbresponse', 3206, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')
 ('nbresponse', 3210, 'CmpD', 'UNMATCHED', 'unmatched', 'unmatched')

```

## 6.8 Flow detection semantics
For the purpose of this section, the flow-expression supplied to **detect()** is viewed as one big flattened expression.

The semantics are defined in an algorithmic form. An implementation does not have to implement the algorithm verbatim as presented here, but the results should be identical to what is defined here.

Trigger event of a flow-expression is defined as an event which appears first in at least one theoretical match of the flow-expression. There may be many theoretical trigger events for a given flow-expression.

Flow evaluation is defined in terms of attempts to match the flow-expression starting from different positions in the trace.

- The order in which different starting positions are attempted depends on the chosen mode of operation.
- Each evaluation attempt searches for the **first non-empty match of the entire flow-expression**. Empty matches are not admitted. (It’s similar to SVA cover property on sequential property.)
- If there are multiple matches of the whole flow-expression at the same matching point, the match containing the largest amount of constituent records is the one reported as the match.
- If there is no match for the entire flow-expression, an incomplete match may optionally be reported. “Incomplete match” is a non-empty partial match that could theoretically be extended to a complete match if there was more data in the trace. If there are multiple “incomplete matches”, the one with the largest amount of constituent records will be reported. Note that there is always at least one incomplete match - the one that contains solely the trigger event.
- In the previous bullets, if more than one [complete/incomplete] match has that largest amount of constituent records, the choice of the one reported is implementation-dependent.

### 6.8.1 Flow detection modes
As one of the methods to disambiguate record correlation, flow evaluation may operate in multiple modes: 

- OVERLAPPING options - these options allow/disallow overlapping matches. Two matches are said to overlap when the initial point of one is between the initial and the matching point of the other.
    - If OVERLAPPING_MATCHES (default) is set, overlapping matches are allowed.
    - If NO_OVERLAPPING_MATCHES is set, overlapping matches are disallowed.

![a](./assets/overlap_occurrence_flow_def.png)

![a](./assets/overlap_occurrence.png)

![a](./assets/none_overlap_occurrence.png)
 
- If OVERLAPPING_MATCHES is set and overlapping matches contain the same record(s), these options control which of the matches is given preference: the one that has the earliest initial point, or the one that has the latest initial point.
    - EXTEND_EARLIEST_FIRST - prefer a match having earlier initial point.
    - EXTEND_LATEST_FIRST - prefer a match having later initial point.
 
    ![a](./assets/extend_occurrences_flow_def.png)
    
    ![a](./assets/overlapping_trace_data.png)

    ![a](./assets/extend_earliest_first_occ.png)

    ![a](./assets/extend_latest_first_occ.png)
    

- If NO_OVERLAPPING_MATCHES is set:
    - ON_OVERLAP_DISCARD_OLD - a trigger event encountered while another evaluation attempt is in flight causes the existing attempt to fail immediately; a new attempt is started from the newly encountered trigger event.
    - ON_OVERLAP_DISCARD_NEW - a trigger event encountered while another evaluation attempt is in flight is immediately reported as non-match and no new evaluation attempt is started from it.

    ![a](./assets/extend_occurrences_flow_def.png)

    ![a](./assets/on_overlap_discard_new_trace_rec.png)

    ![a](./assets/on_overlap_discard_new_flow_occ.png)

    ![a](./assets/on_overlap_discard_old_trace_rec.png)

    ![a](./assets/on_overlap_discard_old_flow_occ.png)


### 6.8.2 Flow detection operation
The algorithm performs evaluation attempts one by one.

All records are initially designated as “unused”. As evaluation progresses and matches are found, the constituent records are marked as “used” and won’t be able to participate in another match, but still can cause an abort action.

Each evaluation attempt selects a starting position in the order dictated by the operation mode. All records are initially designated as “potential starting points”. As evaluation progresses, records that get marked as “used” are automatically unmarked as “potential starting points”, i.e. get removed from further consideration as starting positions. Records may get their “potential starting point” mark removed even if they are not “used”. E.g., in **NO_OVERLAPPING_MATCHES** mode all records that appear between the first and last records of any previously reported "COMPLETE" or INCOMPLETE] match are excluded from further consideration as starting positions.

A single evaluation attempt proceeds as follows:

1. Select a valid starting position for the evaluation attempt among the records marked as “potential starting points”:
    1. OVERLAPPING_MATCHES | EXTEND_EARLIEST_FIRST: first appearance of a trigger event
    1. OVERLAPPING_MATCHES | EXTEND_LATEST_FIRST: last appearance of a trigger event
    1. NO_OVERLAPPING_MATCHES | ON_OVERLAP_DISCARD_NEW: first appearance of a trigger event
    1. NO_OVERLAPPING_MATCHES | ON_OVERLAP_DISCARD_OLD: first appearance of a trigger event

The selected trigger event is the trigger event of the current attempt.

1. Iteratively examine records in the order of appearance from the selected trigger event. Assume a special “end-of-trace” record marking the end of the trace records. For each record R, the following actions are performed in the specified order: 

    1. If R is an abort event, the corresponding branches assume that the flow-expressions in the scope of the abort condition have failed to match and terminate.
    If as a result, the entire flow-expression is determined to fail (all evaluation branches have terminated), the current attempt is declared as failed. Nothing gets reported. No records get their “used” mark changed. The trigger event of the attempt is unmarked as “potential starting point”.
    1. If R is not marked as “used” , one of the following actions is performed in the specified order:
        - If R is a trigger event in NO_OVERLAPPING_MATCHES | ON_OVERLAP_DISCARD_OLD mode: the current attempt is declared as incomplete; evaluation branch with largest amount of constituent records is reported as incomplete.
        - If R can extend any branch of the evaluation attempt (according to the semantics of operators in the flow-expression), it does so on all such branches.
            - If as a result the evaluation attempt completes matching the entire flow-expression: the attempt succeeds. If there are multiple matches: the one with the largest number of constituent events is declared as the resulting match. The constituent events are marked as “used”. In NO_OVERLAPPING_MATCHES mode all records between the trigger event of the current attempt and R are unmarked as “potential starting points”.
        - If R is an end-of-trace: the current attempt is declared as incomplete. The evaluation branch with the largest amount of constituent records is reported. The constituent events are marked as “used”. In NO_OVERLAPPING_MATCHES mode all records appearing between the trigger event of the current attempt and R are unmarked as “potential starting points”.
        - Otherwise: R is ignored.

As can be seen, each trigger event can start evaluation attempt at most once. Therefore, the overall flow evaluation is guaranteed to eventually terminate.

After all evaluation attempts have been exhausted, the trace records have been classified:
1. Belonging to a complete evaluation attempt
1. Belonging to an incomplete evaluation attempt
1. Unused

***Notes:***
- Current implementation doesn’t necessarily select the evaluation branch with the largest amount of constituent records.
- Also, **NO_OVERLAPPING_MATCHES** | **ON_OVERLAP_DISCARD_NEW** is not producing the result according to the specification when there is an incomplete match. First incomplete match in this case will hide all further possible matches.

### 6.8.3 Flow detection semantics versions
Two versions are currently supported - 'v1' and 'v2'.  'v2' is well defined semantics, described earlier, while 'v1' in multiple cases is not well defined.

'v2' is set as a default mode of flow detection operation. The semantics version can be controlled by global configuration:
``` py

config.detect.semantics = 'v1'

```
Examples emphasizing the differences between versions:

Example 1:
``` py

flow = seq(A, one_of(seq(B, D), C))
# Trace: ABC

```
v2: a complete match 'AC' will be detected

v1: **no** complete match will be detected

Example 2:
``` py

flow = one_of(seq(A, C), seq(A, B))
# Trace: ABAC

```
v2: the complete matches 'AB' and 'AC' will be detected

v1: the behavior is undefined and only one complete match will be detected.

-----------------

# 7 UTDB Coverage
UTDB Coverage includes the following coverage elements:

- Covergroup - a container of Coverpoints, and cross coverage elements
- Coverpoint - an element that represents some context that has related values that need to be looked for and counted
- Coverpoint Bins - represents the values that need to be checked in the related Coverpoint
- Cross Coverage- represents a set of bins that is built out of cross product between multiple Coverpoints' bins

The Coverage API includes 2 global methods:

- **covergroup()** - to create new Covergroup object
- **fetch_coverage()** - to collect coverage data, save it to a file or return it in a Results object.

## 7.1 Global Coverage methods
### 7.1.1 covergroup method
The **covergroup()** method is used to create new Coverage Group object. **covergroup()** method is global. It accepts a name parameter and returns a Covergroup object.

***Syntax:***

<cover_group> = covergroup(<name>[, instance=<instance_name>, location=(<file_abs_path>,<line_number>)] )

***Returns:*** Covergroup object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | String | The name of the group that will appear in the results |
| **instance** | String | The instance name of the specific covergroup that will appear in the result coverage tree under the covergroup node with the coverage of that instance. |
| **location** | python tuple: (String, Number) | Absolute path to the file and line number of the Covergroup definition in the source code (used for back-annotation in EDA tools). Optional argument. Extracted automatically if not provided by user. |

***Notes:***
If multiple instances of a covergroup exist, and the instance attribute is provided to enable per-instance coverage collection, the merging of coverage from all instances into the covergroup coverage is done automatically by EDA coverage converters from the UCIS format. The merged coverage appears in the coverage result tree under the covergroup node in EDA coverage analysis tools.

***Code Example:***
``` py

# create new coverage group object
cg1 = covergroup('Cg1')

# create two instances of covergroup Cg2
cg2_1 = covergroup('Cg2', instance="a.b.c[1].Cg2")
cg2_2 = covergroup('Cg2', instance="a.b.c[2].Cg2")

# create covergroup with user-defined location
cg3 = covergroup('Cg3', location=('/nfs/.../covdef.py', 25))


```

### 7.1.2 fetch_coverage method
The **fetch_coverage()** method is used to collect coverage data, save it to a file or return it in a Results object. It accepts a list of Covergroup objects that need to be used in the collection process, and some other flags related to what to do with the results e.g. in which format to save the file, and other coverage related information

***Syntax:***

Returning coverage data in results object:

<cov_results> = fetch_coverage(<covergroup_list>, format=CoverageOutputFormat.RESULT_ITERATOR)

Saving the text file:

fetch_coverage(<covergroup_list>, format=TEXT [, output=<output_dir>] )

Saving the EDA format file:

fetch_coverage(<covergroup_list>, format=<output_format>, testname=<test name>, module=<module name> , instance=<instance_name> [, output=<output_dir>])

***Returns:*** Coverage Results object or None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| covergroup_list | List of Covergroup objects | The Covergroup list that will be used for coverage data collection. |
| **format** | CoverageOutputFormat enum | see [CoverageOutputFormat enum definition](#-coverageoutputformat-enum). ***Default:*** **CoverageOutputFormat.RESULT_ITERATOR** |
| **testname** | String | Used for per-test coverage analysis supported by EDA tools. |
| **module** | String | Used to generate correct coverage hierarchy; required by EDA tools. |
| **instance** | String | Used to generate correct coverage hierarchy; required by EDA tools. |
| **output** | String Directory | Path for the created coverage data file. Default is current dir. |

***Notes:***
- The results object will have records with the following fields:
    - **COVERGROUP_NAME**
    - **COVERPOINT_NAME**
    - **BIN_NAME**
    - **HITCOUNT**
- **testname**, **module** and **instance** are mandatory for EDA format output
- The default files name for **CoverageOutputFormat.TEXT** is "coverage_report.txt". if **module** is specified, the module name will be used for output file name .txt

***Code Example:***
``` py

# collect coverage to results iterator (default)
results = fetch_coverage([cg1])
for row in results:
    print(row.COVERGROUP_NAME, row.COVERPOINT_NAME, row.BIN_NAME, row.HITCOUNT)
 
# coverage data results example
CG1 p1 data[AAA] 7
CG1 p1 data[BBB] 3
CG1 p1 data[CCC] 1
CG1 p3 num[1] 0
CG1 p3 num[2] 2
CG1 p3 num[3] 0
CG1 p3 num[10] 1

```
#### CoverageOutputFormat enum

| Enum Value | Description | 
| -------------- | ---- |
| CoverageOutputFormat.RESULT_ITERATOR (default) | return the data in results object |
| CoverageOutputFormat.TEXT | UTDB proprietary readable text format |
| CoverageOutputFormat.UCIS | Write coverage data to xml file in UCIS format |
| CoverageOutputFormat.VDB | Write coverage data in VDB format (Synopsys) |
| CoverageOutputFormat.UNICOV | Write coverage data in UCD/UCM format (Cadence) |
| CoverageOutputFormat.VDB_AND_UNICOV | Write coverage data in VDB format (Synopsys) and UCD/UCM format (Cadence) in the same invocation of the fetch_coverage method.|

## 7.2 Covergroup object
Covergroup object represents a container of other coverage elements. Covergroup object is created by using the global method covergroup. Covergroup definition is back-annotated for future viewing in EDA coverage analysis tools. Absolute path to file and line number are extracted automatically or may be provided by user in 'location' argument of covergroup method.  

***Covergroup has the following attributes:***
- **name** - returns the name of Covergroup
- **instance** - returns the instance name of Covergroup
- **location** - returns absolute path to the file and line number of the Covergroup definition in the source code

***Covergroup has the following methods:***
- **coverpoint()** - create a new Coverpoint object
- **cross()** - create a cross coverage object
- **coverpoints** - returns list of Coverpoints defined in this Covergroup
- **[]** - dictionary like getter to get Coverpoint from Covergroup by name
- **in** - dictionary like checker if Coverpoint exists in Covergroup by name
- **len** - return the number of coverpoints in the covergroup
- **iterator** - returns iterator of the coverpoints in the covergroup


### 7.2.1 coverpoint method
The **coverpoint()** method is used to create new Coverpoint object. **coverpoint()** method takes multiple parameters that determine its type. The supported Coverpoint types and their related parameters are as follows:

- Value Coverpoint - contains a reference to a UTDB value expression and coverage data automatically collected by the UTDB system. It accepts the following Parameters:

| Parameter Name | Description |
| -------------- | ----------- |
| name (mandatory) | A string name for the Coverpoint; unique in its parent Covergroup |
| values_of (mandatory) | A utdb value expression that is used by the UTDB tool to collect coverage information |
| iff (optional) | A utdb condition to enable filtering invalid trace records from the coverage report |
| collect (optional) | If False, it will not collect coverage for the Coverpoint and the Coverpoint can be used in the cross-coverage definition. ***Default:*** **True** |
 	
- Sampled Coverpoint - used to collect coverage from user sampled values. It accepts the following Parameters:

| Parameter Name | Description |
| -------------- | ----------- |
| name (mandatory) | A string name for the Coverpoint; unique in its parent Covergroup |
| value_type(optional) | DataType enum that specifies the type of sampled data values; ***Default:*** DataType.UINT |
| collect (optional) | If False, it will not collect coverage for the Coverpoint and the Coverpoint can be used in the cross-coverage definition. ***Default:*** **True** |

- Query Coverpoint - contains a reference to a UTDB query (parameterized or not) and coverage data automatically collected by the UTDB system. It accepts the following Parameters:

| Parameter Name | Description |
| -------------- | ----------- |
| name (mandatory) | A string name for the Coverpoint; unique in its parent Covergroup |
| query (mandatory) | A utdb query used to collect coverage information by UTDB tool |
| collect (optional) | If False, it will not collect coverage for the Coverpoint and the Coverpoint can be used in the cross-coverage definition. ***Default:*** **True** |

***Syntax:***

<value_cover_point> = <covergroup>.coverpoint(<name>, values_of=<utdb value expression> [,iff=<utdb boolean expression>] [,collect=<True | False>] [, location=(<file_abs_path>,<line_number>)])

<sample_cover_point> = <covergroup>.coverpoint(<name> [,value_type=<utdb DataType>] [,collect=<True | False>] [, location=(<file_abs_path>,<line_number>)])

<query_cover_point > = <covergroup>.coverpoint(<name>, query=<utdb query> [,collect=<True | False>] [, location=(<file_abs_path>,<line_number>)])

***Returns:*** Coverpoint object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | string | The name of the Coverpoint that will appear in the results. |
| **values_of** | UTDB Value Expression | Will be used to read values from the trace records and collect their hit counts. |
| **iff** | UTDB Boolean expression | Will be used to filter trace records from the Coverpoint hit counts. |
| **collect** | Boolean | If True, collets coverage for the Coverpoint. If False, does not collect coverage for the Coverpoint. ***Default:*** **True** |
| **query** | Query object | If query is not parameterized, a single query runs and its count is reported. If parameterized, runs a query for all possible combinations of parameter’s values and collects their hit counts. |
| **value_type** | DataType enum | The type of sampled data; default is DataType.UINT |
| **location** | Tuple (string, number) | Absolute path to file and line number of the coverpoint definition in the source code (used for back-annotation in EDA tools). Optional argument; extracted automatically if not provided by user. |
		
***Notes:*** 

***Code Example:***
``` py

# create new value Coverpoint object sampling DATA field values
cp1 = cg1.coverpoint('p1', values_of=(trace.all.DATA), location=('/nfs/iil/.../covdef.py', 110))
 
# create new value Coverpoint object sampling DATA field values only if the record type is cpurequest
cp2 = cg.coverpoint('p2', values_of=(trace.all.DATA), iff = record_type(trace.cpurequest))
 
# create new sampled Coverpoint of value type STRING
cp3 = cg.coverpoint('p3', value_type=DataType.STRING, location=('/nfs/iil/.../covdef.py', 200))
 
# create parametrized query coverpoint
cp4 = cg.coverpoint('p4', query=where((trace.all.DATA == P('data')) &
record_type(trace.cpurequest))

```

### 7.2.2 cross method
The **cross()** method is used to create a new cross coverage object. Cross Coverage uses existing Coverpoints or bins and creates cross product bins for their values.

***Syntax:***

<cross_cover> = <covergroup>.cross(<name>, <cover_element> [,cover element ]…)

***Returns:*** CrossCover object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | String | The name of the cross that will appear in the results. |
| cover_element | Coverpoint or Bin | Will be used to create cross product bins for the elements bin values. |

***Notes:***

***Code Example:***
``` py

# create new value Coverpoint object sampling DATA field values
cp_opcode = cg1.coverpoint('opcodes', values_of=trace.all.OPCODE)
cp_data = cg1.coverpoint('data1', values_of= trace.all.DATA)
 
cross = cg1.cross('OPCODE_DATA', cp_opcode, cp_data)

```

### 7.2.3 name attribute getter
The **name** attribute getter returns the name of the Covergroup.

***Syntax:***

<string> = <covergroup>.name

***Returns:*** Covergroup name

***Parameters:***

***Notes:***

***Code Example:***
``` py

cg = covergroup("my_covergroup")
print(cg.name)

```

### 7.2.4 coverpoints method
The **coverpoints()** method returns list of coverpoint objects from the covergroup

***Syntax:***

<coverpoint_list> = <covergroup>.coverpoints()

***Returns:*** list of Coverpoints

***Parameters:***

***Notes:***

***Code Example:***
``` py

# create new value Coverpoint object sampling DATA field values
cp_opcode = cg1.coverpoint('opcodes', values_of=trace.all.OPCODE)
cp_data = cg1.coverpoint('data1', values_of= trace.all.DATA)
 
cp_list = cg1.coverpoints()

```

### 7.2.5 [] coverpoint getter
The **[]** returns coverpoint by its name.

***Syntax:***

<coverpoint> = <covergroup>[<cp_name>]

***Returns:*** Coverpoint object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| cp_name | String | name of the coverpoint we look for. |

***Notes:***
- The **[]** operator throws exception if coverpoint name does not exists in covergroup (like dictionary ker error exception)

***Code Example:***
``` py

cg = covergroup("Cg1")

cg.coverpoint("p1", values_of=(trace.all.DATA))
cg.coverpoint("p2", values_of=trace.all.OPCODE)
cg.coverpoint("p3", values_of=(trace.all.COREREQID))

print(cg["p1"].name)
cg["p2"].ignore(["Read", "Cmp"])
cp3 = cg["p3"]
bin31 = cp3.bin_per_value("coreid", [range(18,25), range(0,10), range(10,20), range(15,22)])

```

### 7.2.6 in, not in operators key checker
The **in** and **not in** operators are same as in python, They are used to check whether a specific coverpoint name belongs to a covergroup or not

***Syntax:***

<bool> = <cp_name> in <covergroup>
<bool> = <cp_name> not in <covergroup>

***Returns:*** Boolean value based on the results of **in** or **not in**

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| cp_name | String | name of the coverpoint we look for. |
| covergroup | Covergroup object | the covergroup to look in. |

***Notes:***

***Code Example:***
``` py

cg = covergroup("Cg1")

cg.coverpoint("p1", values_of=(trace.all.DATA))
cg.coverpoint("p2", values_of=trace.all.OPCODE)
cg.coverpoint("p3", values_of=(trace.all.COREREQID))

if "p1" in cg:
    print("coverpoint ", cg["p1"].name, " in covergroup ", cg.name )

if "p4" not in cg:
    print("p4 is not coverpoint in covergroup ", cg.name )

```

### 7.2.7 len method
The **len()** method behaves like python len method and returns the number of coverpoints in the covergroup

***Syntax:***

<number> = len(<covergroup>)

***Returns:*** number of coverpoints

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| covergroup | Covergroup object | the covergroup to look in. |

***Notes:***

***Code Example:***
``` py

cg = covergroup("Cg1")

cg.coverpoint("p1", values_of=(trace.all.DATA))
cg.coverpoint("p2", values_of=trace.all.OPCODE)
cg.coverpoint("p3", values_of=(trace.all.COREREQID))

print("Number of coverpoints: ", len(cg))

```

### 7.2.8 iterator
The **iterator** behaves like python iterator and returns coverpoint object in each iteration

***Syntax:***

for cp in <covergroup>:
    <do something with cp>

***Returns:*** coverpoint objects in each iteration

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| coverpoint | Coverpoint object | one of the coverpoints from the covergroup. |
| covergroup | Covergroup object | the covergroup to iterate on. |

***Notes:***

***Code Example:***
``` py

cg = covergroup("Cg1")

cg.coverpoint("p1", values_of=(trace.all.DATA))
cg.coverpoint("p2", values_of=trace.all.OPCODE)
cg.coverpoint("p3", values_of=(trace.all.COREREQID))

for cp in cg:
    print(cp.name)            

```

## 7.3 Coverpoint object
Coverpoint object represents an observed element that counts its value hits for its bins.

Coverpoint object is created by using the Covergroup’s coverpoint method (see Covergroup for more information).

***It has multiple methods to collect coverage values:***
- Automatic value coverage collection - for value expression (value Coverpoint)
- Parameterized query results v coverage collection (query Coverpoint)
- Manual value sampling by the user (sampled Coverpoint)
Coverpoint contains Bins that are used to collect coverage counters.

***Coverpoint has the following attributes:***
- **name** - returns the name of Coverpoint
- **covergroup** - returns parent Covergroup object

***Coverpoint has the following methods:***
- **bin** - method to create a single bin for counting how many times bin values were detected (hit)
- **bin_per_value** - method to create bin array (a single bin for each value in the value list or for each combination of a parameter’s values)
- **auto_gen_bin** - method to automatically generate bins on integral value Coverpoints
- **sample** - method to sample user values in a sampled Coverpoint type
- **ignore** - method to specify values that should be excluded from all coverpoint’s bins

Coverpoint definition is back-annotated for future viewing in EDA coverage analysis tools. File name and line number are extracted automatically or may be provided by user in the **location** argument of the coverpoint method.  

### 7.3.1 bin method
A **bin()** is a unit of coverage measurement. The Coverpoint’s bin method is used to create a new bin object. It accepts a name argument and a list of values or a dictionary of parameter’s values to include in the bin, and returns a Bin object.

***Syntax:***

<bin> = bin(<name>,<list_of_values>)

<bin> = bin(<name>, <dict_of_params_values>)

***Returns:*** Bin object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | String | The name of the bin that will appear in the results. |
| list_of_values | Python list | List of values that correlates to the Coverpoint type. |
| dict_of_params_values | Python dictionary | Dictionary with key: Utdb Bindparam object, value: list of values of parameter. |

***Notes:***
- Repeated values are counted only once.
- Values can be added using multiple calls with the same bin name.
- There will be single line in the coverage results for this bin.

***Code Example:***
``` py

# create string bin with 2 values
bin1 = cp1.bin("str_bin",['WRITE', 'MODIFY'])
 
# output bins
str_bin
 
# create numeric bin using specific numbers and ranges
bin2 = cp2.bin("num_bin",[1,2,range(10,30),40])
 
# output bins
num_bin
 
#create single bin which contains 14 (2 x 7) combinations based on values of 2
#parameters
#str: ['WRITE', 'MODIFY']
#num: [1,2,range(10,15)] 
bin3 = cp1.bin("str_num",{P('str'): ['WRITE', 'MODIFY'],
P('num') : [1,2, range(10,15))
 
#output bins
str_num

```

### 7.3.2 bin_per_value method (for Value cover point)
Value Coverpoint’s **bin_per_value()** method creates a bin array. This means that a bin will be created for each value in the given value list. It accepts a name parameter and a list of values to create bins for, and returns a Bin object.

***Syntax:***

<bin> = bin_per_value(<name>,<list_of_values>)

***Returns:*** Bin object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | String | The name of the bin that will appear in the results. |
| list_of_values | Python list | List of values that correlates to the Coverpoint type and will have an explicit bin for each of them. |

***Notes:***
- Repeated values are ignored.
- Values can be added using multiple calls with the same bin name.
- A specific bin for each value will be created.

***Code Example:***
``` py

# create string bin array with 2 values
bin1 = cp1.bin_per_value('str_bin',['WRITE', 'MODIFY'])

# output bins
str_bin[WRITE]
str_bin[MODIFY]

# create numeric bin array using specific numbers and ranges
bin2 = cp1.bin_per_value ('num_bin',[1,2,range(10,30),40])

# output bins
num_bin[1]
num_bin[2]
num_bin[10]
…
num_bin[29]
num_bin[40]

```

### 7.3.3 bin_per_value method (for Query cover point)
Query Coverpoint’s **bin_per_value()** method creates a bin array. This means that a bin will be created for each combination of parameter’s values in the given parameter dictionary. It accepts a name argument and a dictionary {Bindparam : list of values}  to create bins for, and returns a Bin object.

***Syntax:***

<bin> = bin_per_value(<name>,<dict_of_param_values>)

***Returns:*** Bin object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | String | The name of the bin that will appear in the results. |
| dict_of_param_values | Python Dictionary | Dictionary with key: Utdb Bindparam object, value: list of values of parameter. |

***Notes:***
- Repeated values are ignored.
- Values can be added using multiple calls with the same bin name.
- A specific bin for each combination of parameter’s values will be created.

***Code Example:***
``` py
#create 14 (2 x 7) bins for all possible combinations of 2 parameters
#str: ['WRITE', 'MODIFY']
#num: [1,2,range(10,15)] 
 
bin1 = cp1.bin_per_value("str_num",{
  P('str'): ['WRITE', 'MODIFY'],
  P('num') : [1,2, range(10,15)]
 })
 
# output bins
str_num[WRITE,1]
str_num[WRITE,2]
str_num[WRITE,10]
…
str_num[WRITE,14]
str_num[MODIFY,1]
str_num[MODIFY,2]
str_num[MODIFY,10]
…
str_num[MODIFY,14]

```

### 7.3.4 auto_gen_bin method
If the Coverpoint's expression type is integral (numeric, e.g. uint64), the Coverpoint’s **auto_gen_bin()** method automatically creates a bin array for the whole Coverpoint values space or for a specified range. The whole space or the specified range is automatically distributed evenly auto_bin_max sub-spaces (default is 64).

***Syntax:***

<bin> = auto_gen_bin(<name>, [range=<bin_range>], [auto_bin_max=64])

***Returns:*** Bin object

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| name | String | The name of the bin that will appear in the results. |
| **range** | Python Range | Use python range method to specify the range to create bins for. |
| **auto_bin_max** | Number | maximum number of sub-spaces to automatically create for the whole space. |

***Notes:***
- For both integral and non integral Coverpoint's expression type, if bins are not specified, a bin is created for each distinct value of the expression that is monitored - in the data source.

***Code Example:***
``` py

# create integral value Coverpoint
cover_point = cg.coverpoint('p5', values_of=(trace.all.COREREQID))
 
# auto create 5 bins for range 0 to 23
cp5.auto_gen_bin('auto', range(0,23), auto_bin_max=5)
 
# output bins
auto[0:4]
auto[4:9]
auto[9:14]
auto[14:18]
auto[18:23]

```

### 7.3.5 sample method
The **sample()** method is called by the user to sample values and count their hits. The sample method accepts a value parameter based on the Coverpoint's expected values and type.

***Syntax:***

<cover_point>.sample(<value>)

***Returns:*** Boolean. It returns False if the sampled combination does not belong to the coverage space or is ignored.

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| value | Value (Depends on Coverpoint values type) | The value is checked against the bins that were defined for the Coverpoint, and the values hit counts are collected. |

***Notes:***

***Code Example:***
``` py

# sampling string value
cp1.sample('WRITE')
 
# sampling number
cp1.sample(289)

```

### 7.3.6 ignore method
The **ignore()** method is called by the user to specify values that should be excluded from coverage space.

***Syntax:***

<cover_point>.ignore(<values>)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| values | Value list | List of values or ranges that correlates to the Coverpoint type |

***Notes:***
- In case of auto-generated bins, the specification of ignored values does not affect the distribution of values into bins. In other words, value distribution into bins happens first regardless of whether certain values are ignored or not.

***Code Example:***
``` py

# ignore string values
cp1.ignore(['WRITE', ‘MODIF’])
 
# ignore numbers
cp1.ignore([range(0,3), 289, range(500,700)])

```

***Note:*** In case of auto-generated bins, the specification of ignored values does not affect the distribution of values into bins. In other words, value distribution into bins happens first regardless of whether certain values are ignored or not
``` py

# create 5 bins for range(0,23)
bin_core = values_cp.auto_gen_bin('coreid', range(1,23), 5)
 
# distribution values into bins
coreid[0:3], coreid[4:7], coreid[8:11], coreid[12:15], coreid[16:22]
 
# ignore values
values_cp.ignore([1, range(7,11), 20])
 
# final output bins
# bin name     values in bin   
coreid[0:3]     => [0,2,3]
coreid[4:7]     => [4,5,6]
coreid[8:11]    => [11]
coreid[12:15]   => [12,13,14,15]
coreid[16:22]   => [16,17,18,19,21,22]

```

## 7.4 Cross Coverage object
Cross Coverage uses existing Coverpoints or bins and creates cross product bins for their values.

***Cross has the following attributes:***
- **name** - returns the name of Cross obejct
- **covergroup** - returns parent Cross object

***Cross has the following methods:***
- **sample()**    - for sampling user values in cases where the cross uses Sampled Coverpoint or Bins
- **cross_bin()** - for specifying user-defined cases where the cross uses Sampled or Value Coverpoints or Bins
- **ignore()**    - for exclude crossed values in cases where the cross uses Sampled or Value Coverpoints or Bins

### 7.4.1 sample method
The **sample()** method is called by the user to sample values and count their hits.

There are two possible ways to provide a sampled cross combination:
- The **sample()** method accepts multiple parameters based on the cross object number of cover elements, where the elements are of sampled Coverpoint type. The value needs to be in the order of the cover elements used in the cross creation.
- The **sample()** method accepts a dictionary of Coverpoints and their values to eliminate the need to keep the order of the values parameters.

***Method 1***

***Syntax:***

<cross_cover>.sample (<value>,<value>, …)

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| value | Value | Depends on Coverpoint values type. The value is checked against the bins that were defined for the Coverpoint, and the values hit counts are collected. |


***Method 2***

***Syntax:***

<cross_cover>.sample(<coverpoints_values>){,<cp5>:<value5>, …, <cp3> : <value3>})

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| coverpoints_values | Dictionary of <Coverpoint>:<value> | Dictionary Key: Coverpoint object, Value: value of value_type defined in correspondent Coverpoint. The value is checked against the bins that were defined for the Coverpoint, and the values hit counts are collected. |

***Notes:***

***Code Example:***
``` py

# sampling cross data of string cover element and number cover element 
cp_str = cg.coverpoint(...)
sp_num = cg.coverpoint(...)
cross_cov = cg.cross('STR_x_NUM', cp_str, cp_num)
 
# method 1
cross_cov.sample('WRITE', 35)
 
# method 2
cross_cov.sample({cp_num: 25, cp_str: 'READ'})

```

### 7.4.2 ignore method
The ignore method is called by the user to specify crossed values that should be excluded from all Coverpoint’s bins.  The ignore method accepts a dictionary of Coverpoints and their values.

***Syntax:***

<cross_cover>.ignore(<coverpoitns_value_list>{<cp1>: <list of values or ranges>, <cp2>: <list of values or ranges>, …, <cpN> : <list of values or ranges>})

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| coverpoitns_value_list | Dictionary of <Coverpoint>:<value_list> | Dictionary Key: Coverpoint object, Data: List of values that correlates to the Coverpoint type. Each value from the list is checked against the bins that were defined for the Coverpoint. |

### 7.4.3 cross_bin method
The cross_bin method is called by the user to specify crossed values that should be included to cross coverage space.  The cross_bin method accepts a dictionary of Coverpoints and their values.

***Syntax:***

<cross_cover>.cross_bin(<coverpoitns_value_list>{<cp1>: <list of values or ranges>, <cp2>: <list of values or ranges>, …, <cpN> : <list of values or ranges>})

***Returns:*** None

***Parameters:***

| Parameter Name | Type | Description |
| -------------- | ---- | ----------- |
| coverpoitns_value_list | Dictionary of <Coverpoint>:<value_list> | Dictionary Key: Coverpoint object, Data: List of values that correlates to the Coverpoint type. Each value from the list is checked against the bins that were defined for the Coverpoint. |

***Notes:***

***Code Example:***
``` py

cg = covergroup("Cg1")            
cp1 = cg.coverpoint("p1", values_of=trace.all.OPCODE)                
cp1.bin_per_value("op", ["Write", "CmpD", "Read", "Cmp"])        

cp2 = cg.coverpoint("p2", values_of=(trace.all.COREREQID))
cp2.bin_per_value("coreid", [range(18,25), range(0,10)])

cr1 = cg.cross("p1_x_p2", cp1, cp2)
cr1.cross_bin({cp1: ["Read", "Write"], cp2: [range(5,13)]})
cr1.cross_bin({cp1: ["Cmp"], cp2: [0,1]})
cr1.cross_bin({cp1: ["XXX"], cp2: [2,3]})
cr1.cross_bin({cp1: ["Read"], cp2: [20,22,25]})

cr1.ignore({cp1: ["Read", "XXX"], cp2: [5, 6, 20]})

# output
Cross: p1_x_p2
        op[Read]_x_coreid[7]                                                 1
        op[Read]_x_coreid[8]                                                 0
        op[Read]_x_coreid[9]                                                 1
        op[Write]_x_coreid[5]                                                0
        op[Write]_x_coreid[6]                                                1
        op[Write]_x_coreid[7]                                                0
        op[Write]_x_coreid[8]                                                1
        op[Write]_x_coreid[9]                                                0
        op[Cmp]_x_coreid[0]                                                  0
        op[Cmp]_x_coreid[1]                                                  1
        op[Read]_x_coreid[22]                                                2
```


# 8. Global Configuration
Global Configuration enables several setting to globally control all or parts of the API's behavior.

It is arranged in several categories and several settings in each category.

The interface for the setting includes python script utdb global object, or dedicated environment variable.

## 8.1 Configuration Categories and settings

Use onfig.help() method for most up to date configurations.

***Configuration options table:***

| Category | Setting | Default | Description |
| -------- | ------- | ------- | ----------- |
| logging | console_log_level | LogLevel::LOG_ERROR | The log level for messages going to the console/stdout. |
| logging | logfile_log_level | LogLevel::LOG_INFO | The log level for messages going to the log file. |
| logging | logfile_path | "" | The log file path. Hostname and PID may optionally get appended to it based on the append_host_pid_to_logfile_path setting. |
| logging | append_host_pid_to_logfile_path | True | If true, the current host name and process id are added to the name of the log file as a means of uniquification. |
| logging | disallow_logfile_log_level_reduction | False | Disallows reduction of the logfile verbosity level. Useful when externally forcing high verbosity via cmd line or environment, disregarding the settings made by a script programmatically. |
| logging | disallow_logfile_path_change | False | Disallows modification of the logfile path. Useful when externally forcing the log file path via cmd line or environment, disregarding the settings made by a script programmatically. |
| planner | default_execution_async | False | Enables the query plan to execute individual queries of the plan asynchronously by default, unless overridden by explicit parameters of the query plan. If false, a multi-query query-plan will execute queries sequentially one after another on the same thread on which the plan is executed. |
| planner | default_execution_parallel | False | Enables the query plan to parallelize individual subtasks of a given query by default, unless overridden by explicit parameters of the specific query plan. If false, all subtasks required for a query execution will run on the same thread where the query result is requested. |
| planner | max_async_workers | std::thread::hardware_concurrency() | Max count of asynchronously queries executed by a query plan. |
| planner | backend_query_out_buffer_size | 50000 | Buffer size, counted in number-of-records, for results of a paged backend fetch operation during parallel query execution. |
| planner | detect_out_buffer_size | 1000 | Buffer size, counted in number-of-records, for results of a paged flow-detection operation. |
| coverage | enable_async_execution | True | Enables the coverage collection to use asynchronous query execution. |
| general | default_backend | "logdb" | The backend used by default if connection path does not contain backend prefix, and fo UTDB generation unless specified otherwise in the connection string. |
| detect | semantics | 'v2' | Flow detection semantics: 'v2' - well defined, 'v1' - not well defined. |
| detect | memory_limit | '8GB' | Limits the memory used by flow detection. Minimum - 1KB. Exceeding the limit yields a flow detection error. |
| detect | partial_results_on_error | False | Allows to suppress a flow detection error and return partial results for debugging purposes only. Do not use it for production code, since results are not guaranteed to be repeatable between runs. |

***Log level values:***

| Log Level         | value |
| ----------------- | ----- |
| LOG_NONE          | 0     |
| LOG_FATAL         | 1     |
| LOG_ERROR         | 2     |
| LOG_WARN          | 3     |
| LOG_INFO          | 4     |
| LOG_DATA          | 5     |
| LOG_LONGDATA      | 6     |
| LOG_DEBUG         | 7     |
| LOG_TRACE         | 8     |
| LOG_DEBUGDATA     | 9     |
| LOG_LONGDEBUGDATA | 10    |


## 8.2 Configuration control methods
There are 3 methods to control the values of Global Configurations settings:

- Python script - uses global utdb config object to set values for the different settings.

``` py

# using config global object attributes
config.logging.logfile_log_level=10
config.logging.console_log_level=2

# using config global object set_from_cmd_line() method
config.set_from_cmd_line("--utdb.logging.logfile_log_level=10")

```

- User app command line options using set_from_cmd_line API.
``` py

call: user_app.py --utdb.logging.logfile_log_level=10 --utdb.logging.console_log_level=2
 
```

- Environment variable - set environment variable UTDB_CONFIG similar to command line options.
``` py

setenv UTDB_CONFIG "--utdb.logging.logfile_log_level=10 --utdb.logging.console_log_level=2"

```
