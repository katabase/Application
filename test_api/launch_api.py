from lxml import etree
import requests
import click
import json
import sys


# --------------------------------------------------------------------------------
# launch a quick query on the katapi with a dict containing query parameters
# to use: `python test_api/launch_api.py -p '{"dict": "with", "query": "params"}'`
# --------------------------------------------------------------------------------


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

  print(r.headers)
  print(r.status_code)

  # parsing the results allows us to check for errors
  # for practical reasons, print the client-side mistakes
  if r.headers["Content-Type"] == "application/xml; charset=utf-8":
    tree = etree.fromstring(r.content)
    out = etree.tostring(tree)
    if r.status_code == 422:
      print(out)
  else:
    out = r.json()
    if r.status_code == 422:
      print(out)
  return None


if __name__ == "__main__":
  query()
