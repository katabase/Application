from lxml import etree
import requests
import click
import json
import sys


# ---------------------
# test the katapi
# --------------------


@click.command()
@click.option("-p", "--params", help="query parameters")
def query(params=None):
  """
  test the katabase API
  :param params: the query parameters
  """
  url = "http://127.0.0.1:5000/katapi"
  if not params:
    click.echo("you must input research parameters")
    sys.exit(1)
  params = json.loads(params)
  r = requests.get(url, params=params)

  if r.headers["Content-Type"] == "application/xml; charset=utf-8":
    print(r.headers)
    print(type(r.content))
    print(r.status_code)
    tree = etree.fromstring(r.content)
    out = etree.tostring(tree)
  else:
    out = r.json()
    print(out)
  return None


if __name__ == "__main__":
  query()
