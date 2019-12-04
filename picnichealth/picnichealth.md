# PicnicHealth

PicnicHealth is a service that collects and consolidates an individual's health records. Resources such as conditions,
measurements, providers, visits, medications, imaging and notes are available. Each individual's data is composed of
JSON documents, one per resource. Objects contain references to other resource documents via UUID properties. Documents
such as conditions and measurements also make references via OMOP concept codes to a document containing an index
of the concept codes and their details.

## Documents

[Schema](picnichealth.schema.json)

[Example](example/picnichealth.json)