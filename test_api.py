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
  print(params)
  print(type(params))
  url = "http://127.0.0.1:5000/katapi"
  if not params:
    click.echo("you must input research parameters")
    sys.exit(1)
  params = json.loads(params)
  r = requests.get(url, params=params)
  r = r.json()
  print(r)
  return None


if __name__ == "__main__":
  query()
