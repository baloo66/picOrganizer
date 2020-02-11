# picOrganizer


## Summary

`picOrganizer` reads all `.jpg`/`.jpeg` files in a given directory and tries to extract date/time information. The order in which this information is retrieved:

* EXIF tag `EXIF DateTimeOriginal`
* EXIF tag `EXIF DateTimeDigitized`
* EXIF tag `GPS GPSDate` and `GPS GPSTimeStamp`
* EXIF tag `Image DateTime`
* filesystem creation timestamp

The timestamp is interpreted and the target fo the file is constructed:

`<targetpath>/<year>/<month>/<day>/filename`

where `year`, `month` and `day` are extracted from the timestamp.

## Usage

### copy files

```{python}
python picOrganizer --src C:\temp\source --dst C:\temp\destpath
```

### move files

```{python}
python picOrganizer --src C:\temp\source --dst C:\temp\destpath --move
```