# Let's Read Asia Chef
The script `sushichef.py` downloads the Let's Read Asia content,
converts it for use in Kolibri, then uploads it into Kolibri Studio so that later
the content can be imported into Kolibri and used offline.


## Installation
1. Install the system prerequisites `ffmpeg` and `imagemagick` by following the
   [prerequisite install instructions](https://ricecooker.readthedocs.io/en/latest/installation.html#software-prerequisites).
2. Install [Python 3](https://www.python.org/downloads/) if you don't have it already.
3. Make sure you also have `pip` installed by running the command `pip --help`
   in a terminal, and if missing [install it](https://pypi.python.org/pypi/pip).
4. Create a Python virtual environment for this project:
   * Install the virtualenv package: `pip install virtualenv`
   * The next steps depends on whether you're using UNIX or Windows:
      * For UNIX systems (Linux and Mac):
         * Create a virtual env called `venv` in the current directory using the
           following command: `virtualenv -p python3  venv`
         * Activate the virtualenv called `venv` by running: `source venv/bin/activate`.
           Your command prompt should change and show the prefix `(venv)` to
           indicate you're now working inside `venv`.
         * **Checkpoint**: Try running `which python` and confirm the Python in
           is use the one from the virtual env (e.g. `venv/bin/python`) and not
           the system Python. Check also `which pip` is the one from the virtualenv.
      * For Windows systems:
         * Create a virtual env called `venv` in the current directory using the
           following command: `virtualenv venv`.
         * Activate the virtualenv called `venv` by running `.\venv\Scripts\activate`
         * **Checkpoint**: Try running `python --version` and confirm the Python
           version that is running is the same as the one you downloaded in step 2.
5. Run `pip install -r requirements.txt` to install the required Python libraries
   inside the virtual env.


## Credentials
To upload content using a `ricecooker` script, you must first obtain your 
[Studio user authentication token](https://studio.learningequality.org/settings/tokens).
Save this token somewhere safe on your computer and treat it like a password:
do not share it with anyone, don't send it in emails, and don't save it in git.


## Usage
To run the Let's Read Asia content import script you can call the
Python script `sushichef.py` as follows

    python sushichef.py -v --token=<YOURTOKENHERE>

This will run the chef in verbose mode using the Studio token credentials provided.
For more details about the various command line arguments and options, consult
[the docs](https://ricecooker.readthedocs.io/en/latest/chefops.html#ricecooker-cli).


---

## About
A sushi chef script is responsible for importing content into Kolibri Studio.
The [ricecooker](https://github.com/learningequality/ricecooker) library provides
all helper methods necessary for uploading the content to Kolibri Studio.
The ricecooker docs can be found [here](https://ricecooker.readthedocs.io/en/latest/).

This repo includes two sample chef scripts in `examples/openstax_sushichef.py` (json)
and `examples/wikipedia_sushichef.py` (html). To find more code examples, search
for [`sushi-chef-*` on github]https://github.com/search?q=org%3Alearningequality+sushi-chef-%2A)
to see all the sushi chef scripts. They are all example of how to extract,
transform, and upload content from various sources of openly licensed content.


## Instructions and channel rubric
A sushi chef script has been created for you in `sushichef.py` to help you get
started on the import of the Let's Read Asia content.

1. Start by looking at the **channel spec** that describes the target channel structure,
   licensing information, and tips about content transformations that might be necessary.
2. Add the code necessary to create this channel by modifying the `construct_channel`
   method of the chef class defined in `sushichef.py`.

Use the following rubric as a checklist to know when your sushi chef script is done:

### Main checks
1. Does the channel correspond to the spec provided?
2. Does the content render as expected when viewed in Kolibri?

### Logistic checks
1. Is the channel uploaded to Studio and PUBLISH-ed?
2. Is the channel imported to a demo server where it can be previewed?
3. Is the information about the channel token, the studio URL, and demo server URL
   on notion card up to date? See the [Studio Channels table](https://www.notion.so/761249f8782c48289780d6693431d900).
   If a card for your channel yet doesn't exist yet, you can create one using
   the `[+ New]` button at the bottom of the table.

### Metadata checks
1. Do all nodes have appropriate titles?
2. Do all nodes have appropriate descriptions (when available in the source)?
3. Is the correct [language code](https://github.com/learningequality/le-utils/blob/master/le_utils/resources/languagelookup.json)
   set on all nodes and files?
4. Is the `license` field set to the correct value for all nodes?
5. Is the `source_id` field set consistently for all content nodes?
   Use unique identifiers based on the source website or permanent url paths.

### Code standards
1. Does the section `Usage` in this README contain all the required information
   for another developer to run the script?
   Document and extra credentials, env vars, and options needed to run the script.
2. Is the Python code readable and succinct?
3. Are clarifying comments provided where needed?


## Kolibri content development workflow
Running the sushichef script is only one of the steps in the Kolibri content
development workflow. Here is the full picture:

```
                ricecooker      studio         kolibri demo server
  SPEC----->----CHEF----->------PUBLISH---->---IMPORT using token and REVIEW
   \  \         /                                                    /
    \  `clarif.´                                                    /
     \                                                             /
      `---------------- spec compliance checks -------------------´
```

It is your responsibility as the chef author to take this content channel all the way
through this workflow and make sure that the final channel works in Kolibri.
For details about each step in the workflow see the section
[Kolibri content workflows](https://ricecooker.readthedocs.io/en/latest/platform/content_workflows.html)
in the docs.
