# Fitbit

Fitbit data is a JSON document per participant containing the entirety of their Fitbit record. Resources include steps, 
distance, sleep, and heart rate, among others. Resources are a list of dictionaries, almost all of which contain a 
'dateTime' and a 'value' detailing that record for that observed day. The exceptions to this rule are heart rate, 
sleep, weight and body fat. These resources have more details properties but are still essentially lists of 
observations.

### Heart Rate

Heart rate is a list of periodic observations throughout a day, either with second or minute granularity. We collect
second-by-second data where possible so each day's data object will contain a list of objects detailing the observed
heart rate for each second throughout the day's observation.

`Note:` These observations will be extensive, with roughly a three second period between observed values, for as long
as the individual wore the observing device.

### Sleep

Sleep details a number of different data per night of observed sleep. Phases of sleep are detailed chronologically, 
categorized by "wake", "light", "deep", or "rem" sleep throughout the observed night. Summaries of each phase and 
the time spent in each are also detailed.

### Weight and Body Fat

Weight and body fat observations include additional data about the device doing the collection.

## Documents

[Schema](fitbit.schema.json)

[Example](example/fitbit.json)

