# MANGO - simple async ODM for MongoDB.  
  

## User Guide

### Installation

You can install `mangodm` via `pip`.
```bash
pip install mangodm
```

### Initialization
Firstly need to connect to MongoDB.  
```python
from mangodm import connect_to_mongo

MONGODB_CONNECTION_URL = ""
DATABASE_NAME = ""

async def main():
	await connect_to_mongo(MONGODB_CONNECTION_URL, DATABASE_NAME)

```

Don't forgot to close connection.
```python
from mangodm import connect_to_mongo, close_connection

MONGODB_CONNECTION_URL = ""
DATABASE_NAME = ""

def befor_down():
	close_connection()

  

async def main():
	await connect_to_mongo(MONGODB_CONNECTION_URL, DATABASE_NAME)

```

### Defining Collection

Inherit `Document` class and describe its fields to defining new collection.
```python
from mangodm import Document

class User(Document):
	name: str
	age: int

```

Before start to use collection you need to register it.
```python
from mangodm import Document

class User(Document):
	name: str
	age: int

User.register_collection() # IMPORTANT

```

Also you can add special configuration to collection. To do this add subclass `Config`.

**Config Parameters**
* collection_name - collection name in mongoDB.
* excludeFields - list of names fields which don't saving in DB.
* excludeFieldsResponse - list of names fields which don't include in response.

```python
from mangodm import Document

class User(Document):
	name: str
	password: str
	age: int
	points: int

	class Config:
		collection_name = "users"
		excludeFields = ["points"]
		excludeFieldsResponse: ["password"]

User.register_collection()

```

### Create new document
For create new document just create new object of collection class and call `create()` method from it.
```python
from mangodm import Document

class User(Document):
	name: str
	age: int

User.register_collection()

async def main():
	mike = User(name="Mike", age=23)
	await mike.create()

```

After creating you can get document `id`. ID is `str` type.
```python
async def main():
	mike = User(name="Mike", age=23)
	await mike.create()
	print(mike.id)

```

### Get documents from MongoDB

  

To get one document use method - `get`. Parameters for this method is filter for finding document. Parameter convert to JSON and put to MongoDB method `find_one`.

Method return class object or `none` if querying document doesn't exist.

  

```python
from mangodm import Document

class User(Document):
	name: str
	age: int

User.register_collection()

async def main():
	mike = await User.get(name="Mike")
		if mike:
			print(mike.id)
	
	anna = await User.get(id="6561a3851492b7e9d9a9533e")
	if anna:
		print(anna.age)
```

  

To get all documets which suitable for finding filter use method - `find`. This method has same paramrtrs how method `get`. `find` method return list of class objects, list can be empty.

  

```python
from mangodm import Document

class User(Document):
	name: str
	age: int

User.register_collection()

async def main():
	users = await User.find() # get all documents if no parametrs
	for user in users:
		print(user.id)

```

### Updating document

To update editing use method `update`.
```python
from mangodm import Document

class User(Document):
	name: str
	age: int
	
User.register_collection()

async def main():
	mike = await User.get(name="Mike")
	if mike:
		print(mike.id)
		mike.age = 24
		await mike.update()
```

### Deleting document

To delete document use method `delete`.

```python
from mangodm import Document

class User(Document):
	name: str
	age: int

User.register_collection()

async def main():
	mike = await User.get(name="Mike")
	if mike:
		await mike.delete()

```

### Response documents

You can convert your document to JSON. For this use method `to_response()`.

```python
from mangodm import Document

class User(Document):
	name: str
	age: int

User.register_collection()

async def main():
	mike = await User.get(name="Mike")
	if mike:
		print(mike.to_response())

```
