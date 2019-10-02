# PicnicHealth

PicnicHealth is a service that collects and consolidates an individual's health records. Resources such as conditions,
measurements, providers, visits, medications, imaging and notes are available. Each individual's data is composed of
JSON documents, one per resource. Objects contain references to other resource documents via UUID properties. Documents
such as conditions and measurements also make references via OMOP concept codes to a document containing an index
of the concept codes and their details.

## Documents

|Resource|Schema|Example|
|--------|:-----:|:------:|
|Care Site|[Schema](careSite.schema.json)|[Example](example/careSite.json)|
|Concept|[Schema](concept.schema.json)|[Example](example/concept.json)|
|Condition|[Schema](condition.schema.json)|[Example](example/condition.json)|
|Condition Readable|[Schema](conditionReadable.schema.json)|[Example](example/conditionReadable.json)|
|Drug|[Schema](drug.schema.json)|[Example](example/drug.json)|
|Drug Readable|[Schema](drugReadable.schema.json)|[Example](example/drugReadable.json)|
|Location|[Schema](location.schema.json)|[Example](example/location.json)|
|Measurement|[Schema](measurement.schema.json)|[Example](example/drug.json)|
|Measurement Readable|[Schema](measurementReadable.schema.json)|[Example](example/measurementReadable.json)|
|PDF File|[Schema](pdfFile.schema.json)|[Example](example/pdfFile.json)|
|Provider|[Schema](provider.schema.json)|[Example](example/provider.json)|
|Visit|[Schema](visit.schema.json)|[Example](example/visit.json)|
|Note|[Schema](note.schema.json)|[Example](example/note.json)|