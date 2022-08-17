# Application

This repository contains the web publication application of the corpus of manuscript 
sales catalogues. This branch contains the current stable version of the website. See
`versionX.X.X` for the older versions.

---

## Getting started :

- First, download this repository. Using command lines, clone the repository with :
```bash
git clone https://github.com/katabase/Application.git
cd Application
```
- Then, create a virtual environment and activate it :
```bash
python3 -m venv my_env
source my_env/bin/activate
```
- Now, you have to install dependencies :
```bash
pip install -r requirements.txt
```
- You can finally launch the application :
```bash
python3 run.py
```

---

## Use the `KatAPI`

`KatAPI` is an API that allows the automated retrieval of data from the project in 
`json` or `xml-tei`.

### Quick start

The endpoint for the API is **`https://katabase.huma-num.fr/katapi?`**. The arguments 
provided by the client are added after this endpoint; the application will process
thoses arguments and send back a response in the requested format (`json` or `xml-tei`,
the default being `json`). If there is an error on the client side (unauthorized 
parameters or values) or on the server side (unexpected error), a response will be
issued in `json` or `xml-tei` (depending on the client's request) describing the 
query parameters, the time of the query and the error that occured.

### Possible query parameters and authorized values

#### HTTP methods

The only **authorized HTTP method** is `GET`.

#### Possible parameters

The **possible parameters** are:
- **`format`**: the format of the API's response body. Possible values are:
	- `json`: **this is the default value**.
	- `tei`: return an `xml-tei` response.
- **`level`**: the requested data's level. Possible values are:
	- `itm`: data is retrieved at item level. **This is the default value.**
	- `cat_data`: statistical data on one or several catalogues will be retrieved
		- this value is incompatible with the `orig_date` parameter.
	- `cat_full`: a complete catalogue encoded in `xml-tei` will be retrieved
		- if this value is provided, then the only other authorized parameters are
		  `format=tei` and `id` (with `id` matching `CAT-\d+`).
- **`id`**: the identifier of the item or catalogue(s) to retrieve 
  (depending on the value of `level`). If this parameter is provided, data will only
  be retrieved for a single catalogue or catalogue entry. This parameter cannot be used
  together with the `name` parameter. Possible values are:
	- if the query is at item level, a catalogue entry's `@xml:id`. This identifier
	  is a string that matches the pattern: `CAT_\d+_e\d+_d\d+`.
	- the query is run at catalogue level (`level=cat_full` or `level=cat_data`), a 
	  catalogue's `@xml:id`. This identifier is a string that matches the pattern:
	  `CAT_\d+`.
- **`name`**: if the `id` parameter is not supplied, the name of the catalogue(s) or
  catalogue entry(ies) to retrieve. Note that this parameter can, and will, return 
  several items. Possible values:
	- if `level=itm`, the `tei:name` being queried. Only the last name in 
	  the `tei:name` is indexed in the search engine and only this one will yield a 
	  result. If a first name and a last name are provided, no result can be yield,
      since the first name is not indexed.
	- if `level=cat_stat`, the catalogue type (to be found in 
	  `(TEI//sourceDesc/bibl/@ana` in the `xml` representation of a catalogue).
	  Possible values are:
		- 'LAC': Vente Jacques Charavay,
		- 'RDA': Revue des Autographes,
		- 'LAV': Catalogue Laveredet,
		- 'AUC': Auction sale
		- 'OTH': not yet in use in our dataset
- **`sell_date`**: the sale date for a manuscript or a catalogue. Values must match
  the regular expression `\d{4}(-\d{4})?`: a year in `YYYY` format or a year range in
  `YYYY-YYYY` foramat.
- **`orig_date`**: the date a manuscript item was created. This parameter is only 
  authorized if `level=itm`. Values must match  the regular expression `\d{4}(-\d{4})?`: 
  a year in `YYYY` format or a year range in `YYYY-YYYY` foramat.

### Return formats

#### At `cat_full` level

In this case, a complete catalogue encoded in `xml-tei` will be returned. It is 
the same as [any catalogue of the project](https://github.com/katabase/Application/blob/main/APP/data/CAT_000148_tagged.xml),
except that a `tei:note` has been added to the `TEI//sourceDesc/publicationStmt` in 
order to describe the context in which the file was retrieved: the query parameters,
the date and time of the query and the HTTP status code of the response are retrieved.

#### At `cat_stat` level

In this case, two possible response formats are possible: `json` and `xml-tei`.

The `json` response looks like:
```python
{
    "head": {
        "query": {
            "format": "json",
            "id": "CAT_000362",
            "level": "cat_stat"
        },
        "query_date": "2022-08-17T13:17:29.808084",
        "status_code": 200
    },
    "results": {
        "CAT_000362": {
            "cat_type": "LAC",
            "currency": "FRF",
            "high_price_c": 102.0,
            "high_price_items_c": {
                "CAT_000362_e27096": 102.0
            },
            "item_count": 106,
            "low_price_c": 1.27,
            "mean_price_c": 9.810188679245282,
            "median_price_c": 4.59,
            "mode_price_c": 3.06,
            "sell_date": "1875",
            "title": "Vente Jacques Charavay, ao\u00fbt 1875, n\u00ba 185",
            "total_price_c": 1039,
            "variance_price_c": 194.2879773228907
        }
    }
}
```

The `xml` response is similar, but uses `tei` elements and includes a more complete
`teiHeader`:

```xml
<?xml version='1.0' encoding='utf-8'?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>KatAPI query results</title>
        <respStmt>
          <resp>File created automatically by KatAPI, an API developped as part of the</resp>
          <orgName>
            <ref target="https://katabase.huma-num.fr/">MSS / Katabase project.</ref>
          </orgName>
        </respStmt>
        <respStmt>
          <resp>Production of the source data:</resp>
          <orgName>Projet e-ditiones</orgName>
          <orgName>Katabase</orgName>
          <orgName> Manuscript SaleS Catalogue</orgName>
        </respStmt>
        <funder>
          <orgName>Université de Neuchâtel</orgName>
          <orgName>Université de Genève</orgName>
          <orgName>École normale Supérieure</orgName>
        </funder>
      </titleStmt>
      <publicationStmt>
        <ab>
          <date type="file-creation-date" when-iso="2022-08-17T13:40:44.217345">2022-08-17T13:40:44.217345</date>
          <ref type="http-status-code" target="https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200">200</ref>
          <note>Original data made available under Creative Commons Attribution 2.0 Generic (CC BY 2.0)</note>
          <table>
            <head>Query parameters</head>
            <row>
              <cell role="key" xml:id="level">level</cell>
              <cell role="key" xml:id="id">id</cell>
              <cell role="key" xml:id="format">format</cell>
            </row>
            <row>
              <cell role="value" corresp="level">cat_stat</cell>
              <cell role="value" corresp="id">CAT_000362</cell>
              <cell role="value" corresp="format">tei</cell>
            </row>
          </table>
        </ab>
      </publicationStmt>
      <sourceDesc>
        <p>Sources may come from different documents. See the corresponding XML-TEI catalogues on 
          <ref target="https://github.com/katabase/Application/tree/main/APP/data">Github</ref>
          for detailed description of the sources.
        </p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="search-results">
        <list>
          <head>Search results</head>
          <item ana="CAT_000362">
            <label>CAT_000362</label>
            <term key="title">Vente Jacques Charavay, août 1875, nº 185</term>
            <term key="cat_type">LAC</term>
            <term key="sell_date" type="date">1875</term>
            <term key="item_count">106</term>
            <term key="currency">FRF</term>
            <term key="total_price_c" type="constant-price">1039</term>
            <term key="low_price_c" type="constant-price">1.27</term>
            <term key="high_price_c" type="constant-price">102.0</term>
            <term key="mean_price_c" type="constant-price">9.810188679245282</term>
            <term key="median_price_c" type="constant-price">4.59</term>
            <term key="mode_price_c" type="constant-price">3.06</term>
            <term key="variance_price_c" type="constant-price">194.2879773228907</term>
            <term key="high_price_items_c" type="constant-price" ana="CAT_000362_e27096">102.0</term>
          </item>
        </list>
      </div>
    </body>
  </text>
</TEI>
```

#### At `itm` level

The `json` response is as follows:

```python
{
    "head": {
        "query": {
            "format": "json",
            "level": "itm",
            "name": "s\u00e9vign\u00e9",
            "orig_date": "1500-1800",
            "sell_date": "1800-1900"
        },
        "query_date": "2022-08-17T13:53:02.110102",
        "status_code": 200
    },
    "results": {
        "CAT_000273_e234_d1": {
            "author": "S\u00c9VIGN\u00c9",
            "date": "1695-08-09",
            "desc": "L. a. s. (\u00e0 Lamoignon); Nantes, 9 ao\u00fbt 1695, 3 p. in-4",
            "format": 4,
            "number_of_pages": 3.0,
            "price": null,
            "sell_date": "1891",
            "term": 7
        }
    }
}
```

And the `xml` file looks like this (the `teiHeader` is omitted here and in the next:

```xml
<?xml version='1.0' encoding='utf-8'?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <!-- the teiHeader is omitted, since it looks much like the
         previous one -->
  </teiHeader> 
  <text>
    <body>
      <div type="search-results">
        <list><head>Search results</head><item n="108" xml:id="CAT_000204_e108">
          <num type="lot">108</num>
          <name type="author">BEETHOVEN (L. van)</name>
          <trait>
            <p>le grand compositeur de musique.</p>
          </trait>
          <desc xml:id="CAT_000204_e108_d1"><term ana="#document_type_9">L. s.</term> à M. M. Schlesinger, à Berlin; Vienne, <date when="1820-05-31">31 mai 1820</date>, <measure type="length" unit="p" n="2">2 p.</measure> <measure type="format" unit="f" ana="#document_format_4">in-4</measure>, cachet</desc><note>Curieuse lettre sur ses ouvrages. Il leur accorde le droit de vendre ses compositions en Angleterre, y compris les airs écossais, aux conditions indiquées par lui. Il s'engage à leur livrer dans trois mois trois sonates pour le prix de 90 florins qu'ils ont fixé. C'est pour leur être agréable qu'il accepte un si petit honoraire. « Je suis habitué à faire des sacrifices, la composition de mes OEuvres n'étant pas faite seulement au point de vue du rapport des honoraires, mais surtout dans l'intention d'en tirer quelque chose de bon pour l'art.»</note>
        </item>
        </list>
      </div>
    </body>
  </text>
</TEI>
```

#### Error message formats

When an error occurs, here's how it will look like in `json`:

```python
{
    "head": {
        "query": {
            "api": "Durga Mahishasuraparini",
            "format": "json",
            "id": "CAT_0001_e0001_d0001",
            "name": "Guyan Yin",
            "sell_date": "200000"
        },
        "query_date": "2022-08-17T13:49:44.808688",
        "status_code": 422
    },
    "results": {
        "__error_type__": "Invalid parameters or parameters combination",
        "error_description": {
            "format": "The format must match: (tei|json)",
            "id_incompatible_params": "Invalid parameters with parameter id: ['sell_date']",
            "name+id": "You cannot provide both a name and an id",
            "sell_date": "The format must match: \\d{4}(-\\d{4})?",
            "unallowed_params": "Unallowed parameters for the API: ['api']"
        }
    }
}
```

And in `xml`, an error will look like this:

```xml
<?xml version='1.0' encoding='utf-8'?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader> 
    <!-- the teiHeader is omitted, since it looks much like the  
         previous one -->
  </teiHeader>
  <text>
    <body>
      <div type="error-message">
        <list>
          <head>Invalid parameters or parameters combination</head>
          <item ana="no_name+id">
            <label>no_name+id</label>
            <desc>You must specify at least a name or an id</desc>
          </item>
          <item ana="sell_date" corresp="sell_date">
            <label>sell_date</label>
            <desc>The format must match: \d{4}(-\d{4})?</desc>
          </item>
        </list>
      </div></body>
  </text>
</TEI>
```

### Examples

Here are some URL examples and their meaning:
- `https://katabase.huma-num.fr/katapi?level=itm&name=s%C3%A9vign%C3%A9&sell_date=1800-1900&orig_date=1500-1800&format=json`:
  all catalogue items whose author is `Sévigné`, sold between 1800 and 1900 and 
  written between 1500 and 1800, in `json`.
- `https://katabase.huma-num.fr/katapi?level=itm&id=CAT_000204_e108_d1&format=tei`:
  the catalogue item with an `@xml:id` corresponding to `CAT_000204_e108`, in `tei`.
- `https://katabase.huma-num.fr/katapi?level=cat_stat&name=RDA&format=json`:
  statistics about all `RDA` catalogues in `json`
- `https://katabase.huma-num.fr/katapi?level=cat_stat&name=RDA&sell_date=1800-1900&format=json`:
  statistics about all `RDA` catalogues sold between 1800 and 1900 in `json`.

---

## Workflow

<img src="images/workflow.png" alt="Katabase workflow diagram" title="Katabase Workflow" width="70%" height="50%"/>

---

## Website updates and description of the git branches

The structure of the git repository is as follows:
- [`main`](https://github.com/katabase/Application) for the current, stable version of the 
  Katabase app
- [`dev`](https://github.com/katabase/Application/tree/dev) for the unstable version of the
  app, in developpment and not running online.
- [`versionX.X.X`](https://github.com/katabase/Application/tree/version1.0.0) are archive
  repositories to document the former versions of the Katabase app. There should be as many
  of these branches as there are new versions of the website, and their `X.X.X` code should
  follow the release numbers.

New additions to the website should be done on `dev` and tested before being moved to `main`.
The version of the website visible on `main` should be the same as the version of the website
online (unless, for reasons out of our control, we can't publish a new version of the website
online, but a new version is ready and won't be changed again). Before merging a new version
of the website from `dev` to `main`, the `main` branch should be moved the `versionX.X.X`.
A new release should then be created for the updated version of the website.

---

## Credits

The application was designed by Alexandre Bartz and Paul Kervegan with the help of Simon Gabay, Matthias Gille Levenson and Ljudmila Petkovic.

---

## Cite this repository

## Licence
This work is licensed under [GNU GPL-3.0](./LICENSE).
