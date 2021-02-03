#!/usr/bin/env python
import csv
import os
import sys
import json
from urllib.parse import urlencode
from requests.exceptions import HTTPError
from ricecooker.utils import downloader, html_writer
from ricecooker.chefs import SushiChef
from ricecooker.classes import nodes, files, questions
from ricecooker.config import LOGGER              # Use LOGGER to print messages
from ricecooker.exceptions import raise_for_invalid_channel
from le_utils.constants import exercises, content_kinds, file_formats, format_presets, languages, licenses


# Run constants
################################################################################
CHANNEL_NAME = "Let's Read Asia"                    # Name of channel
CHANNEL_SOURCE_ID = "sushi-chef-lets-read-asia"     # Channel's unique id
CHANNEL_DOMAIN = "reader.letsreadasia.org"          # Who is providing the content
CHANNEL_LANGUAGE = "mul"                            # Language of channel
CHANNEL_DESCRIPTION = "A library of local language children's books" # Description of the channel (optional)
CHANNEL_THUMBNAIL = "https://reader.letsreadasia.org/esm-bundled/images/logo.png" # Local path or url to image file (optional)

# Additional constants
################################################################################

SITE_URL = "https://reader.letsreadasia.org"

API_URL = "https://letsreadasia.appspot.com/api"
API_URL_V2 = "{}/v2".format(API_URL)

ID_LEVEL_0 = "0"
ID_LEVEL_1 = "1"
ID_LEVEL_2 = "2"
ID_LEVEL_3 = "3"
ID_LEVEL_4 = "4"
ID_LEVEL_5 = "5"

LEVELS_IDS = [ID_LEVEL_0, ID_LEVEL_1, ID_LEVEL_2, ID_LEVEL_3, ID_LEVEL_4, ID_LEVEL_5]
LEVELS_NAMES = dict([
  (ID_LEVEL_0, "My first book"),
  (ID_LEVEL_1, "Level 1"),
  (ID_LEVEL_2, "Level 2"),
  (ID_LEVEL_3, "Level 3"),
  (ID_LEVEL_4, "Level 4"),
  (ID_LEVEL_5, "Level 5"),
])
LEVELS_QUERY_VALUES = dict([
  (ID_LEVEL_0, "MY_FIRST_BOOK"),
  (ID_LEVEL_1, "LEVEL_1"),
  (ID_LEVEL_2, "LEVEL_2"),
  (ID_LEVEL_3, "LEVEL_3"),
  (ID_LEVEL_4, "LEVEL_4"),
  (ID_LEVEL_5, "LEVEL_5"),
])

# The chef subclass
################################################################################
class LetsReadAsiaChef(SushiChef):

    channel_info = {                                   # Channel Metadata
        'CHANNEL_SOURCE_DOMAIN': CHANNEL_DOMAIN,       # Who is providing the content
        'CHANNEL_SOURCE_ID': CHANNEL_SOURCE_ID,        # Channel's unique id
        'CHANNEL_TITLE': CHANNEL_NAME,                 # Name of channel
        'CHANNEL_LANGUAGE': CHANNEL_LANGUAGE,          # Language of channel
        'CHANNEL_THUMBNAIL': CHANNEL_THUMBNAIL,        # Local path or url to image file (optional)
        'CHANNEL_DESCRIPTION': CHANNEL_DESCRIPTION,    # Description of the channel (optional)
    }

    def construct_channel(self, *args, **kwargs):
        """
        Creates ChannelNode and build topic tree
        Args:
          - args: arguments passed in on the command line
          - kwargs: extra options passed in as key="value" pairs on the command line
            For example, add the command line option   lang="fr"  and the value
            "fr" will be passed along to `construct_channel` as kwargs['lang'].
        Returns: ChannelNode with the following hierarchy (empty topics are not included):
                  -> Language
                    -> Level
                      -> Tag
                        -> Book
        """
        channel = self.get_channel(*args, **kwargs)  # Create ChannelNode from data in self.channel_info

        books_saved = []
        books_not_saved = []

        try:
          books = fetch_books_list()
        except HTTPError:
          LOGGER.error("Could not fetch all books list")
          return

        books_details = {}
        for book in books:
          master_book_id = book["masterBookId"]
          language_id = book["languageId"]

          try:
            book_detail = fetch_book_detail(master_book_id, language_id)
          except HTTPError:
            LOGGER.error("Could not fetch a book detail for \n {}".format(book))
            books_not_saved.append(book)
            continue

          books_details[book_detail["id"]] = book_detail

          available_languages = book_detail["availableLanguages"]
          for language in available_languages:
            # we already have the book detail for this language
            if language["id"] == language_id:
              continue

            try:
              book_detail = fetch_book_detail(master_book_id, language["id"])
            except HTTPError:
              LOGGER.error("Could not fetch a book detail for \n {}".format(book))
              books_not_saved.append(book)
            else:
              books_details[book_detail["id"]] = book_detail

        books_details_list = list(books_details.values())
        # make sure that languages and levels will be displayed in a correct order
        books_details_list.sort(
          key=lambda book_detail: (book_detail["language"]["name"], book_detail["readingLevel"])
        )

        for book_detail in books_details_list:
          try:
            save_book(book_detail, channel)
            books_saved.append(book_detail)
          except NoFileAvailableError:
            books_not_saved.append(book_detail)

        write_stats(books_saved, books_not_saved)

        raise_for_invalid_channel(channel)  # Check for errors in channel construction

        return channel

# Helpers
################################################################################

class NoFileAvailableError(Exception):
  pass

def fetch_books_list(books=[], last_cursor=""):
  query_params = {
    "cursor": last_cursor,
    "limit": 100 # a limit must be set explicitly otherwise
                 # API returns an empty response
  }
  url = "{}/book/search?{}".format(API_URL_V2, urlencode(query_params))

  response = read_source(url)

  other_books = response.get("other")
  featured_books = response.get("featured")

  if other_books:
    books.extend(other_books)

  if featured_books:
    books.extend(featured_books)

  last_cursor = response.get("cursorWebSafeString")
  if last_cursor:
    fetch_books_list(books, last_cursor)

  return books

def fetch_book_detail(master_book_id, language_id):
  url = "{}/book/preview/language/{}/book/{}".format(API_URL, language_id, master_book_id)
  return read_source(url)

def save_book(book_detail, channel):
  book_id = book_detail["id"]
  book_source_id = get_book_source_id(book_id)
  book_title = book_detail["name"]
  level_id = book_detail["readingLevel"]
  language = book_detail["language"]
  language_id = language["id"]
  tags = book_detail["tags"]
  epub_url = book_detail["epubUrl"]
  pdf_urls = book_detail["pdfUrl"]
  pdf_portrait_url = pdf_urls.get("portraitUrl", "") if pdf_urls else ""
  pdf_landscape_url = pdf_urls.get("landscapeUrl", "") if pdf_urls else ""
  pdf_booklet_url = pdf_urls.get("bookletUrl", "") if pdf_urls else ""
  pdf_url = pdf_portrait_url or pdf_landscape_url or pdf_booklet_url

  if not pdf_url and not epub_url:
    LOGGER.error("No file found for \n {}".format(book_source_id))
    raise NoFileAvailableError()

  book_files = []
  if pdf_url:
    pdf_file = files.DocumentFile(path=pdf_url)
    book_files.append(pdf_file)
  if epub_url:
    epub_file = files.EPubFile(path=epub_url)
    book_files.append(epub_file)

  book = nodes.DocumentNode(
    source_id=book_source_id,
    title=book_title,
    license=licenses.PUBLIC_DOMAIN, # TODO: get a real license and copyright holder
    files=book_files
  )

  language_topic = get_or_create_language_topic(language, channel)
  level_topic = get_or_create_level_topic(level_id, language_id, language_topic)

  if not tags:
    level_topic.add_child(book)
    return

  for tag in tags:
    tag_topic = get_or_create_tag_topic(tag, language_id, level_id, level_topic)
    tag_topic.add_child(book)

def get_or_create_language_topic(language, channel):
  language_id = language["id"]
  language_title = language["name"]
  language_source_id = get_language_source_id(language_id)

  for child in channel.children:
    if child.source_id == language_source_id:
        return child

  topic = nodes.TopicNode(source_id=language_source_id, title=language_title)
  channel.add_child(topic)

  return topic

def get_or_create_level_topic(level_id, language_id, language_topic):
  level_title = LEVELS_NAMES[level_id]
  level_source_id = get_level_source_id(language_id, level_id)

  for child in language_topic.children:
    if child.source_id == level_source_id:
        return child

  topic = nodes.TopicNode(source_id=level_source_id, title=level_title)
  language_topic.add_child(topic)

  return topic

def get_or_create_tag_topic(tag, language_id, level_id, level_topic):
  tag_id = tag["id"]
  tag_title = get_tag_name(tag, language_id)
  tag_source_id = get_tag_source_id(language_id, level_id, tag_id)

  for child in level_topic.children:
    if child.source_id == tag_source_id:
        return child

  topic = nodes.TopicNode(source_id=tag_source_id, title=tag_title)
  level_topic.add_child(topic)

  return topic

def read_source(url):
  source = downloader.read(url)
  return json.loads(source)

def get_book_source_id(book_id):
  return "{}/book/{}".format(SITE_URL, book_id)

def get_language_source_id(language_id):
  return "{}/?{}".format(SITE_URL, urlencode({ "lId": language_id }))

def get_level_source_id(language_id, level_id):
  return "{}/?{}".format(SITE_URL, urlencode({
    "lId": language_id,
    "level": LEVELS_QUERY_VALUES[level_id]
  }))

def get_tag_source_id(language_id, level_id, tag_id):
  return "{}/?{}".format(SITE_URL, urlencode({
    "lId": language_id,
    "level": LEVELS_QUERY_VALUES[level_id],
    "tId": tag_id
  }))

def get_tag_name(tag, language_id):
  tag_localizations = tag["localizations"]
  if str(language_id) in tag_localizations and tag_localizations[str(language_id)]:
    return tag_localizations[str(language_id)]
  return tag["name"]

def write_stats(books_saved, books_not_saved):
  with open("stats.csv", "w", newline="\n") as stats_file:
    writer = csv.writer(stats_file, delimiter=",")

    master_books_ids = list(set([book["masterBookId"] for book in books_saved]))
    books_no_tag = [book for book in books_saved if not book["tags"]]
    books_one_tag = [book for book in books_saved if book["tags"] and len(book["tags"]) == 1]
    books_multiple_tags = [book for book in books_saved if book["tags"] and len(book["tags"]) > 1]

    writer.writerow(["Master books (a master book can have one or more language versions/books)", len(master_books_ids)])
    writer.writerow(["Books", len(books_saved)])
    writer.writerow(["Books without tag", len(books_no_tag)])
    writer.writerow(["Books with one tag", len(books_one_tag)])
    writer.writerow(["Books with multiple tags", len(books_multiple_tags)])

    writer.writerow([])
    writer.writerow(["Books per level"])
    writer.writerow(["Level", "Books", "Books with no tags", "Books with one tag", "Books with multiple tags"])
    for level_id in LEVELS_IDS:
      level_books = [book for book in books_saved if str(book["readingLevel"]) == str(level_id)]
      level_books_no_tag = [book for book in level_books if not book["tags"]]
      level_books_one_tag = [book for book in level_books if book["tags"] and len(book["tags"]) == 1]
      level_books_multiple_tags = [book for book in level_books if book["tags"] and len(book["tags"]) > 1]
      writer.writerow([
        LEVELS_NAMES[level_id],
        len(level_books),
        len(level_books_no_tag),
        len(level_books_one_tag),
        len(level_books_multiple_tags)
      ])

    writer.writerow([])
    writer.writerow(["Books not saved"])
    for book in books_not_saved:
      writer.writerow([get_book_source_id(book["id"])])

# CLI
################################################################################
if __name__ == '__main__':
    # This code runs when sushichef.py is called from the command line
    chef = LetsReadAsiaChef()
    chef.main()