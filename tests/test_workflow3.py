#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2016 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2016-06-25
#

"""Test Workflow3 feedback."""

from __future__ import print_function, unicode_literals

import json
import pytest
from StringIO import StringIO
import sys

from util import create_info_plist, delete_info_plist, INFO_PLIST_TEST3

from workflow.workflow3 import Workflow3


@pytest.fixture(scope='module')
def info3(request):
    """Ensure `info.plist` exists in the working directory."""
    create_info_plist(INFO_PLIST_TEST3)
    request.addfinalizer(delete_info_plist)


def test_required_optional(info3):
    """Item3: Required and optional values."""
    wf = Workflow3()
    it = wf.add_item('Title')
    assert it.title == 'Title'
    o = it.obj
    assert o['title'] == 'Title'
    assert o['valid'] is False
    assert o['subtitle'] == ''
    assert set(o.keys()) == set(['title', 'valid', 'subtitle'])


def test_optional(info3):
    """Item3: Optional values."""
    wf = Workflow3()
    it = wf.add_item('Title', 'Subtitle',
                     arg='argument',
                     uid='uid',
                     valid=True,
                     autocomplete='auto',
                     largetext='large',
                     copytext='copy',
                     quicklookurl='http://www.deanishe.net/alfred-workflow',
                     type='file',
                     icon='icon.png')

    o = it.obj
    assert o['title'] == 'Title'
    assert o['valid'] is True
    assert o['autocomplete'] == 'auto'
    assert o['uid'] == 'uid'
    assert o['text']['copy'] == 'copy'
    assert o['text']['largetype'] == 'large'
    assert o['icon']['path'] == 'icon.png'
    assert o['quicklookurl'] == 'http://www.deanishe.net/alfred-workflow'
    assert o['type'] == 'file'


def test_icontype(info3):
    """Item3: Icon type."""
    wf = Workflow3()
    it = wf.add_item('Title', icon='icon.png', icontype='filetype')
    o = it.obj
    assert o['icon']['path'] == 'icon.png'
    assert o['icon']['type'] == 'filetype'


def test_feedback(info3):
    """Workflow3: Feedback."""
    wf = Workflow3()
    for i in range(10):
        wf.add_item('Title {0:2d}'.format(i + 1))

    orig = sys.stdout
    stdout = StringIO()
    try:
        sys.stdout = stdout
        wf.send_feedback()
    finally:
        sys.stdout = orig

    s = stdout.getvalue()

    assert len(s) > 0

    o = json.loads(s)

    assert isinstance(o, dict)

    items = o['items']

    assert len(items) == 10
    for i in range(10):
        assert items[i]['title'] == 'Title {0:2d}'.format(i + 1)


def test_arg_variables(info3):
    """Item3: Variables in arg."""
    wf = Workflow3()
    it = wf.add_item('Title')
    it.setvar('key1', 'value1')
    o = it.obj
    o2 = json.loads(o['arg'])
    assert 'alfredworkflow' in o2
    r = o2['alfredworkflow']
    assert r['variables']['key1'] == 'value1'
    assert 'config' not in r


def test_feedback_variables(info3):
    """Workflow3: feedback variables."""
    wf = Workflow3()

    o = wf.obj
    assert 'variables' not in o

    wf.setvar('var', 'val')
    it = wf.add_item('Title', arg='something')

    assert wf.getvar('var') == 'val'
    assert it.getvar('var') is None

    o = wf.obj
    assert 'variables' in o
    assert o['variables']['var'] == 'val'


def test_rerun(info3):
    """Workflow3: rerun."""
    wf = Workflow3()
    o = wf.obj
    assert 'rerun' not in o
    assert wf.rerun == 0

    wf.rerun = 1

    o = wf.obj
    assert 'rerun' in o
    assert o['rerun'] == 1
    assert wf.rerun == 1


def test_modifiers(info3):
    """Item3: Modifiers."""
    wf = Workflow3()
    it = wf.add_item('Title', 'Subtitle', arg='value', valid=False)
    it.setvar('prevar', 'preval')
    mod = it.add_modifier('cmd', subtitle='Subtitle2',
                          arg='value2', valid=True)
    it.setvar('postvar', 'postval')
    mod.setvar('modvar', 'hello')

    # assert wf.getvar('prevar') == 'preval'
    # Test variable inheritance
    assert it.getvar('prevar') == 'preval'
    assert mod.getvar('prevar') == 'preval'
    assert it.getvar('postvar') == 'postval'
    assert mod.getvar('postvar') is None

    o = it.obj
    assert 'mods' in o
    assert set(o['mods'].keys()) == set(['cmd'])

    m = o['mods']['cmd']
    assert m['valid'] is True
    assert m['subtitle'] == 'Subtitle2'

    r = json.loads(m['arg'])['alfredworkflow']
    assert r['arg'] == 'value2'
    assert r['variables']['prevar'] == 'preval'
    assert r['variables']['modvar'] == 'hello'


def test_item_config(info3):
    """Item3: Config."""
    wf = Workflow3()
    it = wf.add_item('Title')
    it.config['var1'] = 'val1'

    m = it.add_modifier('cmd')
    m.config['var1'] = 'val2'

    o = it.obj
    r = json.loads(o['arg'])['alfredworkflow']

    assert 'config' in r
    assert set(r['config'].keys()) == set(['var1'])
    assert r['config']['var1'] == 'val1'

    assert 'mods' in o
    assert 'cmd' in o['mods']
    r = json.loads(o['mods']['cmd']['arg'])['alfredworkflow']
    assert 'config' in r

    c = r['config']
    assert c['var1'] == 'val2'


def test_default_directories(info3):
    """Workflow3: Default directories."""
    wf3 = Workflow3()
    assert 'Alfred 3' in wf3.datadir
    assert 'Alfred-3' in wf3.cachedir


def test_run_fails_with_json_output():
    """Run fails with JSON output"""
    error_text = 'Have an error'

    def cb(wf):
        raise ValueError(error_text)

    # named after bundleid
    wf = Workflow3()
    wf.bundleid

    stdout = sys.stdout
    sio = StringIO()
    sys.stdout = sio
    ret = wf.run(cb)
    sys.stdout = stdout
    output = sio.getvalue()
    sio.close()

    assert ret == 1
    assert error_text in output
    assert '{' in output


def test_run_fails_with_plain_text_output():
    """Run fails with plain text output"""
    error_text = 'Have an error'

    def cb(wf):
        raise ValueError(error_text)

    # named after bundleid
    wf = Workflow3()
    wf.bundleid

    stdout = sys.stdout
    sio = StringIO()
    sys.stdout = sio
    ret = wf.run(cb, text_errors=True)
    sys.stdout = stdout
    output = sio.getvalue()
    sio.close()

    assert ret == 1
    assert error_text in output
    assert '{' not in output
