
import click
from mh_cli import cli
from time import sleep

from selenium.common.exceptions import TimeoutException
from common import pass_state, init_browser, selenium_options
from mh_pages.pages import RecordingsPage, \
    AdminPage, \
    TrimPage, \
    UploadPage


@cli.group()
def rec():
    """Do stuff with Matterhorn recordings"""


@rec.command()
@click.option('--presenter',
              help="Presenter video")
@click.option('--presentation',
              help="Presentation video")
@click.option('--combined',
              help="Combined presenter/presentation video")
@click.option('--series',
              help="Series title. Should match an existing series.")
@click.option('--title', default='mh-ui-testing upload',
              help="Recording title")
@click.option('--type', default='L01',
              help="Recording type")
@click.option('--email', default='producer@example.edu',
              help="Producer email")
@click.option('-i', '--inbox', is_flag=True,
              help="Use a MH inbox media file")
@click.option('-w', '--workflow', default='DCE-production-upload',
              help="Use a specific workflow definition, e.g. 'DCE-auto-publish'")
@click.option('--trim-later', is_flag=True,
              help="Choose the trimLater option. Only applies to 'DCE-auto-publish' workflow")
#@click.option('--multitrack', is_flag=True,
#              help="If uploading a MULTITRACK file from epiphan")
@selenium_options
@pass_state
@init_browser('/admin')
def upload(state, presenter, presentation, combined,
           series, title, type, email, inbox, workflow, trim_later):
    """Upload a recording from a local path or the inbox"""

    page = RecordingsPage(state.browser)
    sleep(2)

    with page.wait_for_page_change():
        page.upload_recording_button.click()

    page = UploadPage(state.browser)

    if series is not None:
        page.set_series(series)

    page.title_input.type(title)
    page.type_input.type(type)
    page.publisher_input.type(email)

    page.set_upload_files(presenter=presenter,
                          presentation=presentation,
                          combined=combined,
                          is_inbox=inbox)

    page.workflow_select.select_by_value(workflow)
    sleep(1)

    if combined is not None:
        page.multitrack_checkbox.check()
    else:
        page.multitrack_checkbox.uncheck()

    if trim_later:
        page.trim_later_checkbox.check()

    page.upload_button.click()
    page.wait_for_upload_finish()


@rec.command()
@click.option('-f', '--filter',
              help="filter the recording list using the search box; format is field:text, where "
                   "field is one of 'q' (any field), 'title', 'creator', 'seriesTitle', 'contributor', "
                   "'subject', 'language', 'license'")
@click.option('-c', '--count', type=int, default=None,
              help='find and execute up to this many trims; by default this command will execute all '
                   'that it finds')
@selenium_options
@pass_state
@init_browser('/admin')
def trim(state, filter=None, count=None):
    """Execute trims on existing recording(s)"""

    page = AdminPage(state.browser)
    page.recordings_tab.click()
    page = RecordingsPage(state.browser)
    page.max_per_page()
    page.on_hold_tab.click()
    page.refresh_off()
    sleep(3)

    if filter is not None:
        field, value = filter.split(':', 1)
        page.filter_recordings(field, value)

    link_js = [x['href'].split(':', 1)[1] for x in page.trim_links]

    for js in link_js:
        page.js(js)

        page = TrimPage(state.browser)
        sleep(3)

        with page.switch_frame(page.trim_iframe):
            sleep(5)
            page.trim()

        with page.wait_for_page_change():
            page.reload()

        page = RecordingsPage(state.browser)

        if count is not None:
            count -= 1
            if count == 0:
                break
        sleep(5)
