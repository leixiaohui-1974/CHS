# FileAdapterAgent

## Function

A FileAdapterAgent acts as a bridge between a CSV data file and the agent society. It reads a CSV file row by row at each simulation step and publishes the data to a specified topic. This is useful for replaying historical data or feeding sensor data into a simulation.

## Parameters

| Key                 | Type          | Required | Description                                                                                             |
|---------------------|---------------|----------|---------------------------------------------------------------------------------------------------------|
| `filepath`          | `str`         | Yes      | The path to the CSV file to be read.                                                                    |
| `topic_template`    | `str`         | Yes      | The topic to publish the data to.                                                                       |
| `payload_columns`   | `list[str]`   | Yes      | A list of column names from the CSV file whose data should be included in the message payload.          |
| `rename_map`        | `dict`        | No       | A dictionary to rename the columns in the final payload. E.g., `{"level_m": "level"}`. Defaults to `{}`.|

## Publishes To

- **Topic:** The value of the `topic_template` parameter.
- **Payload:** A dictionary where the keys are the column names from `payload_columns` (or their renamed versions from `rename_map`) and the values are the corresponding values from the current row of the CSV file.

## Subscribes To

This agent does not subscribe to any topics.
