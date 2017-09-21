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
from anno.models import Anno
from consumer.catchjwt import encode_catchjwt


DEFAULT_REQUESTS_TIMEOUT = 300
SEARCH_PAGE_SIZE = 500

class CatchSearchClient(object):
    """ perform searches in catch backend; _always_ in AnnotatorJS context."""

    def __init__(self,
                 base_url,     # eg. "http://catch.harvardx.harvard.edu/catch/annotator/search"
                 api_key,
                 secret_key,
                 user=None,
                 timeout=None):

        self.url = base_url
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


    def fullset_size(self, context_id=None):

        # first search to check how many records to retrieve
        params = {
            'limit': 1,
            'offset': 0,
            'contextId': context_id,
        }
        resp = requests.get(
            self.url, params=params, verify=False,
            headers=self.default_headers, timeout=self.timeout)
        resp.raise_for_status()

        search_content = resp.json()
        return search_content['total']


    def fetch_page(self, context_id=None, offset=0, limit=1):

        # first search to check how many records to retrieve
        params = {
            'limit': limit,
            'offset': offset,
            'contextId': context_id,
        }
        resp = requests.get(
            self.url, params=params, verify=False,
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
            click.echo('CONVERSION ERROR: {} -- '.format(e))
            error_list.append(annojs)
            raise e
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
@click.option('--source_url', required=True, help='include http/https')
@click.option('--api_key', required=True)
@click.option('--secret_key', required=True)
@click.option('--user', default='user')
def make_token(source_url, api_key, secret_key, user):

    # create searchClient
    client = CatchSearchClient(
        base_url=source_url, api_key=api_key,
        secret_key=secret_key, user='admin')

    click.echo(client.make_token_for_user(user))



@click.command()
@click.option('--workdir', default='tmp', help='directory for input/output; default=./tmp')
@click.option('--filepath', required=True)
def convert(workdir, filepath):

    with open(filepath, 'r') as f:
        annojs_content = json.load(f)

    # hammering fixes
    annojs_ok = []
    annojs_messed = []
    for c in annojs_content:
        if 'media' in c:
            if len(c['ranges']) > 0:
                if 'start' not in c['ranges'][0]:
                    c['ranges'][0]['start'] = ""
                    c['ranges'][0]['end'] = ""
            annojs_ok.append(c)
        else:
            annojs_messed.append(c)

    # get input filename as base for output filenames
    basename = os.path.basename(filepath)

    # save messed up
    save_to_file(workdir, 'messed_{}'.format(basename), annojs_messed)

    # convert and save
    catcha_filename = 'catcha_{}'.format(basename)
    (catcha_list, error_list) =  convert_and_save(
        json_content=annojs_ok,
        workdir=workdir,
        filename=catcha_filename)



def convert_and_save(json_content, workdir, filename):
    click.echo('workdir({}), filename({}), json_content({})'.format(
        workdir, filename, len(json_content)))

    # convert
    (catcha_list, error_list) = convert_to_catcha(json_content)
    click.echo('............ catcha_list({}), error_list({})'.format(
        len(catcha_list), len(error_list)))

    # save to catcha file
    save_to_file(workdir, filename, catcha_list)

    if len(error_list) > 0:
        save_to_file(workdir,
                     filename='error_{0}.json'.format(filename),
                     json_content=error_list)

    return(catcha_list, error_list)



@click.command()
@click.option('--outdir', default='tmp', help='output DIRECTORY; default=./tmp')
@click.option('--offset_start', default=0,
              help='if not pulling all set, specify offset to start')
@click.option('--source_url', required=True, help='include http/https')
@click.option('--api_key', required=True)
@click.option('--secret_key', required=True)
@click.option('--context_id', required=True)
@click.option('--reuse_outdir/--no_reuse',
              'exist_ok', default=False, help='default=no_reuse')
def pull_all(outdir, offset_start, source_url,
                     api_key, secret_key, context_id,
                     exist_ok):

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
        total_len = client.fullset_size(context_id=search_context_id)
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
    fullset_anno = {}
    more_to_pull = True
    while more_to_pull and page_no < 50000:
        try:
            click.echo('************** pulling page({}), offset({}), limit({})'.format(
                page_no, offset, SEARCH_PAGE_SIZE))
            page_content = client.fetch_page(
                context_id=search_context_id, offset=offset, limit=SEARCH_PAGE_SIZE)
        except Exception as e:
            click.echo('ERRO: {}'.format(e))
            return
        else:
            size = 0
            for c in page_content['rows']:
                if c['id'] in fullset_anno:
                    # sanity check, not supposed to happen (i think)
                    click.echo('GAAAAAAAAAAAAAAAAAAAAAH, duplicate({})'.format(c['id']))
                else:
                    fullset_anno[c['id']] = c
                    size += 1

            current_len += size
            offset += size
            more_to_pull = size > 0
            click.echo('next page_no({}); this batch size({}); current_len({}); more?({})'.format(
                page_no, size, current_len, more_to_pull))
            page_no += 1

    click.echo('FINISH pulling from source, total({})'.format(len(fullset_anno)))

    save_to_file(outdir=outdir,
                 filename='fullset_annojs_{}.json'.format(fullset_name),
                 json_content=list(fullset_anno.values()))


def print_db_info():
    db = getattr(settings, 'DATABASES')
    click.echo('db_host({}) db_name({})'.format(
        db['default']['HOST'], db['default']['NAME']))


@click.command()
@click.option('--workdir', default='tmp', help='output DIRECTORY; default=./tmp')
@click.option('--filepath', required=True, help='filepath for input file')
def push_from_file(workdir, filepath):

    print_db_info()

    with open(filepath, 'r') as f:
        catcha_list = json.load(f)

    # order by id (prevent a reply before associated annotation)
    ordered_catcha_list = sorted(
        catcha_list, key=lambda k: k['id'])

    # mock payload to match permissions
    jwt_payload = {'override': ['CAN_IMPORT']}

    resp = CRUD.import_annos(ordered_catcha_list, jwt_payload)
    failed_list = resp['failed']
    save_to_file(outdir=workdir,
                 filename='fail_to_push_from_file_{}'.format(
                     os.path.basename(filepath)),
                json_content=failed_list)


@click.command()
@click.option('--workdir', default='tmp', help='output DIRECTORY; default=./tmp')
@click.option('--context_id', required=True)
def clear_anno_in_context_id(workdir, context_id):
    print_db_info()

    anno_list = Anno._default_manager.filter(
        raw__platform__context_id=context_id)

    failed_list = []
    for a in anno_list:
        try:
            a.delete()
        except Exception as e:
            click.echo('error deleting({}): {}'.format(a.anno_id, e))
            failed_list.append(a.serialized)

    save_to_file(outdir=workdir,
                 filename='fail_to_delete_{}.json'.format(
                     clean_to_alphanum_only(context_id)),
                json_content=failed_list)


@click.option('--workdir', default='tmp', help='output DIRECTORY; default=./tmp')
@click.command()
def find_reply_to_reply(workdir):
    print_db_info()

    reply_list = Anno._default_manager.all().exclude(
        anno_reply_to_id=None)

    reply_to_reply_list = []
    for r in reply_list:
        for rr in r.replies:
            reply_to_reply_list.append(rr.serialized)

    save_to_file(outdir=workdir,
                 filename='reply_to_reply.json',
                 json_content=reply_to_reply_list)


@click.command()
@click.option('--workdir', default='tmp', help='output DIRECTORY; default=./tmp')
@click.option('--input_filepath_1', required=True)
@click.option('--input_filepath_2', required=True)
def compare_annojs(workdir, input_filepath_1, input_filepath_2):
    """works like file2 contains file1? so set the original set of annojs to
    file1 and the imported set to file2
    """

    with open(input_filepath_1, 'r') as f:
        annojs_list_1 = json.load(f)

    with open(input_filepath_2, 'r') as f:
        annojs_list_2 = json.load(f)

    annojs2 = {x['id']: x for x in annojs_list_2}

    click.echo('dict has ({}) keys'.format(len(annojs2.keys())))

    results = {
        'not_found': [],
        'not_similar': [],
        'passed': [],
    }
    compare = ''
    for a in annojs_list_1:
        if a['id'] in annojs2.keys():
            b = annojs2[a['id']]
            # will compare serialized json
            for x in [a , b]:
                x['uri'] = str(x['uri'])
                # these props were dropped from legacy
                for key in ['archived', 'citation', 'deleted']:
                    try:
                        del x[key]
                    except KeyError:
                        pass  # ok if these already don't exist

                try:  # v2 omits if empty string
                    if len(x['quote']) == 0:
                        del x['quote']
                except KeyError:
                    pass  # ok if these already don't exist


            if AnnoJS.are_similar(a, b):
                results['passed'].append(a)
            else:
                results['not_similar'].append(a)
                results['not_similar'].append(b)
        else:
            results['not_found'].append(a)

    for category in ['not_found', 'not_similar', 'passed']:
        save_to_file(outdir=workdir,
                     filename='{}.json'.format(category),
                     json_content=results[category])




if __name__ == "__main__":

    cli.add_command(pull_all)
    cli.add_command(convert)
    cli.add_command(push_from_file)
    cli.add_command(clear_anno_in_context_id)
    cli.add_command(make_token)
    cli.add_command(compare_annojs)
    cli.add_command(find_reply_to_reply)
    cli()






