#!/usr/bin/env python
import os
import sys

import click
from datetime import datetime
import django
from django.conf import settings
from dotenv import load_dotenv
import fnmatch
import json
import logging
import re
import requests
from urllib.parse import urljoin

#
# set django context
#

# if dotenv file, load it
dotenv_path = os.environ.get('CATCHPY_DOTENV_PATH', None)
if dotenv_path:
    load_dotenv(dotenv_path)

# define settings if not in environment
if os.environ.get("DJANGO_SETTINGS_MODULE", None) is None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "catchpy.settings.dev")

django.setup()


#
# now we can import django app modules
#

from anno.crud import CRUD
from anno.json_models import AnnoJS
from anno.json_models import Catcha
from consumer.catchjwt import encode_catchjwt


DEFAULT_REQUESTS_TIMEOUT = 5
SEARCH_PAGE_SIZE = 100

class CatchSearchClient(object):

    def __init__(self, base_url, api_key,
                 secret_key, user=None, timeout=None):

        self.url = urljoin(base_url, '/catch/annotator/search')
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout or DEFAULT_REQUESTS_TIMEOUT
        self.user = user or 'fake'
        self.default_headers = {
            'Content-Type': 'application/json',
            'x-annotator-auth-token': self.make_token_for_user(self.user),
        }


    def make_token_for_user(self, user):
        return encode_catchjwt(
            apikey=self.api_key, secret=self.secret_key,
            user=user, ttl=86400).decode('utf-8')


    def fullset_size(self, contextId=None):

        # first search to check how many records to retrieve
        params = {
            'limit': 1,
            'offset': 0,
            'contextId': contextId,
        }
        resp = requests.get(
            self.url, params=params,
            headers=self.default_headers, timeout=self.timeout)
        resp.raise_for_status()

        search_content = resp.json()
        return search_content['total']


    def fetch_page(self, contextId=None, offset=0, limit=1):

        # first search to check how many records to retrieve
        params = {
            'limit': limit,
            'offset': offset,
            'contextId': contextId,
        }
        resp = requests.get(
            self.url, params=params,
            headers=self.default_headers, timeout=self.timeout)
        resp.raise_for_status()

        search_content = resp.json()
        return search_content


def convert_to_catcha(annojs_list):
    catcha_list = []
    error_list = []
    for annojs in annojs_list:
        try:
            catcha = Catcha.normalize(annojs)
        except Exception as e:
            error_list.append(annojs)
        else:
            catcha_list.append(catcha)

    return (catcha_list, error_list)


def save_to_file(outdir, filename, json_content):
    path = os.path.join(outdir, filename)
    with open(path, 'w') as f:
        json.dump(json_content, f, sort_keys=True, indent=4)


def clean_to_alphanum_only(name):
    return re.sub(r'[^A-za-z0-9]', '_', name)


@click.group()
def cli():
    pass

@click.command()
@click.option('--outdir', default='tmp', help='output DIRECTORY; default=./tmp')
@click.option('--offset_start', default=0,
              help='if not pulling all set, specify offset to start')
@click.option('--source_url', required=True, help='include http/https')
@click.option('--api_key', required=True)
@click.option('--secret_key', required=True)
@click.option('--context_id', required=True)
@click.option('--catcha_ok/--skip-catcha', default=True,
              help='default is to convert to catcha, as pulled from source')
@click.option('--reuse_outdir/--no_reuse',
              'exist_ok', default=False, help='default=no_reuse')
def pull_from_source(outdir, offset_start, source_url,
                     api_key, secret_key, context_id,
                     catcha_ok, exist_ok):

    # create output dir
    try:
        os.makedirs(outdir, mode=0o776, exist_ok=exist_ok)
    except OSError:
        click.echo('ERROR: outdir already exists({})'.format(outdir))
        return

    # create searchClient
    client = CatchSearchClient(
        base_url=source_url, api_key=api_key,
        secret_key=secret_key, user='admin')

    # search all context_ids?
    search_context_id = None if context_id == 'None' else context_id

    # loop for fetching fullset
    try:
        total_len = client.fullset_size(contextId=search_context_id)
    except Exception as e:
        click.echo('ERROR: unable to fetch fullset_size: {}'.format(e))
        return

    total_pages = int(total_len/SEARCH_PAGE_SIZE)
    if total_len % SEARCH_PAGE_SIZE > 0:
        total_pages += 1

    # save info about this search
    fullset_name = clean_to_alphanum_only(context_id)
    fullset_info = {
        'source_url': source_url,
        'api_key': api_key,
        'context_id': context_id,
        'total_rows': total_len,
    }
    save_to_file(outdir=outdir,
                 filename='info_annojs_{0}.json'.format(fullset_name),
                 json_content=fullset_info)
    click.echo('total_len({}), total_pages({})'.format(total_len, total_pages))


    # need to pull slices of result
    page_no = 1
    current_len = 0
    offset = offset_start
    while current_len < total_len:
        try:
            page_content = client.fetch_page(
                contextId=search_context_id, offset=offset, limit=SEARCH_PAGE_SIZE)
        except Exception as e:
            click.echo('ERRO: {}'.format(e))
            return
        else:
            save_to_file(outdir=outdir,
                         filename='annojs_{0}_{1:06d}.json'.format(
                             fullset_name, page_no),
                         json_content=page_content)

            if catcha_ok:
                convert_and_save(json_content=page_content['rows'],
                                 workdir=outdir,
                                 filename='catcha_{0}_{1:06d}.json'.format(
                                     fullset_name, page_no))

            current_len += int(page_content['size'])
            offset += int(page_content['size'])
            click.echo('next page_no({}); current_len({})'.format(page_no,
                                                                  current_len))
            page_no += 1



@click.command()
@click.option('--workdir', default='tmp', help='directory for input/output; default=./tmp')
@click.option('--context_id', required=True)
def convert(workdir, context_id):
    fullset_name = clean_to_alphanum_only(context_id)
    all_files = sorted(os.listdir(workdir))
    filename_regex = \
            r'^annojs_' + re.escape(fullset_name) + '_(?P<page_no>[0-9]{3})'

    # loop through input files
    for filename in all_files:
        if fnmatch.fnmatch(filename, 'annojs_{}*'.format(fullset_name)):
            # parse filename to get the page number
            match = re.search(filename_regex, filename)
            if match is None:  # skip file
                continue

            page_no = match.group('page_no')

            # read file contents
            path = os.path.join(workdir, filename)
            with open(path, 'r') as f:
                annojs_content = json.load(f)

            # convert and save
            catcha_filename = 'catcha_{0}_{1}.json'.format(fullset_name, page_no)
            convert_and_save(json_content=annojs_content['rows'],
                             workdir=workdir,
                             filename=catcha_filename)


def import_to_db(catcha_list, resp_filepath):
    jwt_payload = {'override': ['CAN_IMPORT']}

    resp = CRUD.import_annos(catcha_list, jwt_payload)



def convert_and_save(json_content, workdir, filename):
    click.echo('workdir({}), filename({}), json_content({})'.format(workdir,
                                                                    filename,
                                                                    len(json_content)))
    # convert
    (catcha_list, error_list) = convert_to_catcha(json_content)
    click.echo('............ catcha_list({}), error_list({})'.format(
        len(catcha_list), len(error_list)))

    # save to catcha file
    save_to_file(workdir, filename, catcha_list)

    if len(error_list) > 0:
        save_to_file(workdir,
                     filename='error_{0}.json'.format(filename),
                     json_context=error_list)



@click.command()
@click.option('--workdir', default='tmp', help='directory for input/output; default=./tmp')
@click.option('--context_id', required=True)
def push_to_target(workdir, context_id):
    fullset_name = clean_to_alphanum_only(context_id)
    all_files = sorted(os.listdir(workdir))
    filename_regex = \
            r'^catcha_' + re.escape(fullset_name) + '_(?P<page_no>[0-9]{3})'

    # loop through input files
    for filename in all_files:
        if fnmatch.fnmatch(filename, 'catcha_{}*'.format(fullset_name)):
            # parse filename to get the page number
            match = re.search(filename_regex, filename)
            if match is None:  # skip file
                continue

            page_no = match.group('page_no')

            # read file contents
            path = os.path.join(workdir, filename)

            click.echo('pushing filename: {}'.format(filename))

            with open(path, 'r') as f:
                catcha_content = json.load(f)

            # sort by anno_id to avoid importing reply before comment
            ordered_catcha_list = sorted(
                catcha_content, key=lambda k: k['id'])

            resp_filename = 'error_{}'.format(filename)
            resp_filepath = os.path.join(workdir, resp_filename)

            import_to_db(ordered_catcha_list, resp_filepath)



if __name__ == "__main__":

    cli.add_command(pull_from_source)
    cli.add_command(convert)
    cli.add_command(push_to_target)
    cli()






