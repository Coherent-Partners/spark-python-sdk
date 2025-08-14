<!-- markdownlint-disable-file MD024 -->

# Folders API

| Verb                              | Description                                                                       |
| --------------------------------- | --------------------------------------------------------------------------------- |
| `Spark.folders.categories.list()` | [Get the list of folder categories](#get-the-folder-categories).                  |
| `Spark.folders.create(data)`      | [Create a new folder with additional info](#create-a-new-folder).                 |
| `Spark.folders.find(name)`        | [Find folders by name, status, category, or favorite](#find-folders-by-criteria). |
| `Spark.folders.update(id, data)`  | [Update a folder's information by ID](#update-a-folders-information).             |
| `Spark.folders.delete(id)`        | [Delete a folder by ID](#delete-a-folder-by-id).                                  |

## Get the folder categories

Presently, the platform supports a preset of folder categories. However, you can
add more categories if needed for your tenant.

To get the list of these categories, you can use the following method:

```py
spark.folders.categories.list()
```

### Returns

```json
[
  { "key": "Medical", "value": "Medical", "icon": "medical.svg" },
  { "key": "Critical Illness", "value": "Critical Illness", "icon": "criticalillness.svg" },
  { "key": "Lifelong Participation", "value": "Lifelong Participation", "icon": "lifelongparticipation.svg" },
  { "key": "Universal Life", "value": "Universal Life", "icon": "universallife.svg" },
  { "key": "Investment Linked", "value": "Investment Linked", "icon": "investmentlinked.svg" },
  { "key": "Annuity", "value": "Annuity", "icon": "annuity.svg" },
  { "key": "Term", "value": "Term", "icon": "term.svg" },
  { "key": "VHIS", "value": "VHIS", "icon": "vhis.svg" },
  { "key": "VHIS + Medical", "value": "VHIS + Medical", "icon": "vhismedical.svg" },
  { "key": "Property & Casualty", "value": "Property & Casualty", "icon": "Property-and-casualty-icon.svg" },
  { "key": "Other", "value": "Other", "icon": "other.svg" }
]
```

> Use `spark.folders.categories.*` methods to manage the folder categories.

## Create a new folder

This method allows you to create a new folder by simply providing a folder name.

> [!IMPORTANT]
> Remember to choose a folder name that is URL-friendly as it will form part of
> a Spark service URI. It's recommended to use lowercase letters and/or hyphens
> instead of whitespaces. Otherwise, special characters like space will be URL-encoded.

### Arguments

You may indicate the folder name as a string.

```py
spark.folders.create('my-folder')
```

Or, you may provide keyword arguments that includes some additional information such as
the folder description, category, start date, launch date, status, and cover image.
In that case, the `name` property is required.

| Property          | Type                       | Description                                             |
| ----------------- | -------------------------- | ------------------------------------------------------- |
| _name_            | `str`                      | The name of the folder.                                 |
| _description_     | `str \| None`              | The description of the folder.                          |
| _category_        | `str \| None`              | The category of the folder (defaults to `Other`).       |
| _start\_date_     | `str \| int \| datetime \| None`| The start date (format: `YYYY-MM-DD[THH:MM:SS.SSSZ]`). |
| _launch\_date_    | `str \| int \| datetime \| None`| The launch date (format: `YYYY-MM-DD[THH:MM:SS.SSSZ]`).|
| _status_          | `str \| None`              | The status of the folder.                               |
| _cover_           | `BinaryIO \| None`         | The cover image of the folder.                          |

```py
from datetime import datetime

spark.folders.create(
  name='my-folder',
  # Optional parameters
  description='This is a folder description',
  category='Medical',
  launch_date=datetime.now().isoformat(),
)
```

### Returns

When successful, the method returns the folder information.

```json
{
  "status": "Success",
  "message": null,
  "errorCode": null,
  "data": {
    "id": "uuid",
    "name": "my-folder",
    "category": "Other",
    "description": "Created by Spark JS SDK",
    "coverImagePath": null,
    "createdAt": "1970-12-03T04:56:56.186Z",
    "isStarred": true,
    "status": "Design",
    "startDate": "1970-12-03T04:56:56.186Z",
    "launchDate": "1980-12-03T04:56:56.186Z",
    "calculationEngines": {
      "count": 0,
      "next": "False",
      "previous": null,
      "message": null,
      "data": [],
      "errorCode": null,
      "status": "Success"
    },
    "sections": [],
    "lastModifiedDate": "1970-12-03T04:56:56.186Z",
    "kanbanStatus": "Test 01",
    "createdBy": "john.doe@coherent.global",
    "activeServiceCount": 0
  }
}
```

Otherwise, it will throw a `SparkApiError`:

- `UnauthorizedError` when the user is not authenticated.
- `ConflictError` when the folder name already exists.
- `UnknownApiError` when the SDK failed to create the folder due to unknown reasons.

> [!IMPORTANT]
> If you are using API key as your authentication method, you should know that API keys
> can't be used to create a folder unfortunately. You will get a `401 Unauthorized` error.
> You should use one of the other methods.
> See [Authentication API](./authentication.md) for more information.

## Find folders by criteria

This method helps you search folders by name, category, or favorite.

### Arguments

You may search a folder by its unique ID.

```py
spark.folders.find('uuid')
```

Or, you can pass in the following parameters as keyword arguments to filter the folders.

| Property   | Type             | Description                               |
| ---------- | ---------------- | ----------------------------------------- |
| _name_     | `str \| None`    | The name of the folder.                   |
| _favorite_ | `bool \| None`   | Whether the folder is marked as favorite. |
| _page_     | `int`            | The page number (defaults to `1`).        |
| _size_     | `int`            | The number of items per page (defaults to `100`).|
| _sort_     | `str`            | The field to sort the folders by (defaults to `-updated`).|

```py
spark.folders.find(favorite=True, page=1, size=10, sort='productName')
```

The above example will return the first 10 favorite folders sorted alphabetically
by the product name.

Additional search parameters can be provided as keyword arguments. For example,
to find all folders that are marked as favorite and belong to the `Medical` category,
you can do the following:

```py
spark.folders.find(favorite=True, category='Medical')
```

### Returns

This method returns all folders with their information that match the search criteria.

```json
{
  "status": "Success",
  "count": 2,
  "next": null,
  "previous": null,
  "message": null,
  "errorCode": null,
  "data": [
    {
      "id": "uuid",
      "name": "my-folder",
      "status": "Design",
      "category": "Medical",
      "description": "something cool is happening here.",
      "coverImagePath": "uuid",
      "createdAt": "2023-06-30T13:27:38.62016Z",
      "createdBy": "john.doe@coherent.global",
      "lastModifiedDate": "2024-03-19T04:58:06.495676Z",
      "isStarred": true,
      "kanbanStatus": "Test 01",
      "startDate": "2023-06-30T00:00:00Z",
      "launchDate": "2023-09-30T00:00:00Z",
      "activeServiceCount": 0,
      "totalServiceCount": 26
    },
    {
      "id": "uuid",
      "name": "my-other-folder",
      "status": "Design",
      "category": "Other",
      "description": "some awesome description.",
      "coverImagePath": null,
      "createdAt": "2023-09-01T17:11:38.381469Z",
      "createdBy": "jane.doe@coherent.global",
      "lastModifiedDate": "2024-01-29T18:41:09.444745Z",
      "isStarred": true,
      "kanbanStatus": "Test 01",
      "startDate": "2023-09-01T00:00:00Z",
      "launchDate": "2023-12-01T00:00:00Z",
      "activeServiceCount": 0,
      "totalServiceCount": 2
    }
  ]
}
```

Check out the [API reference](https://docs.coherent.global/spark-apis/folder-apis/find-folder-by-name)
for more information.

## Update a folder's information

This method allows you to update a folder's information by its ID. Once created,
you can only update the folder's description, category, launch date, start date,
cover, or status.

### Arguments

You must provide the folder ID and the updated folder information, just as in
[creating a new folder](#create-a-new-folder).

```py
spark.folders.update('uuid', description='Updated description')
```

### Returns

The method returns a successful status when the folder is updated.

```json
{
  "status": "Success",
  "data": null,
  "message": null,
  "errorCode": null
}
```

## Delete a folder by ID

This method allows you to delete a folder by its ID.

> [!WARNING]
> This method should be used with caution as it will delete the folder and all its
> content, i.e., its services if any.
>
> Please use with **extreme care** as this action cannot be undone.

### Arguments

You must provide the folder ID as a string.

```py
spark.folders.delete('uuid')
```

### Returns

The method returns a successful status when the folder is deleted.

```json
{
  "status": "Success",
  "data": null,
  "message": null,
  "errorCode": null
}
```

[Back to top](#folders-api) or [Next: Services API](./services.md)
