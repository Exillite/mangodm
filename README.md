# MANGO -  simple async ODM for mongodb.


### Subdocument save like this:
```
"document": {
    "subdocument": {
        "_type": "subdocument",
        "_collection": "{name}",
        "_id": "{id}"
    }
}
```

### Embedded document save like this:
```
"document": {
    "embedded_document": {
        "_type": "embedded_document",
        "_embedded_document": "{embedded_document_name}",
        // ... other data ...
    }
}