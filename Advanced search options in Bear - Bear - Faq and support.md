# Advanced search options in Bear - Bear - Faq and support
To help you find the right notes when you need them, Bear supports a variety of special search commands, operators, and something we call **Special Searches**. 
#biblestudy/devotionals

## Search operators

You can search an exact word sequence by enclosing your sentence with two quote characters `"`. For example:

`"John Appleseed was here"`

To exclude specific words from search result, use the minus symbol `-`. For example, if you want to search for every recipe *without* broccoli, you can type:

`recipes -broccoli`

The minus operator can be also used with quoted sentences or **Special Searches**. For example:

`-"John Appleseed"` or `-@code` 

That will search for notes containing the exact phrase of `John Appleseed` *or* code snippets. Learn more about special searches below.

## Special Searches

Bear also comes with some special search tokens you can use to filter your notes:

* **@tagged** : shows the notes which have at least one tag
* **@untagged**: shows the notes without tags
* **@today**: show the notes modified the current day
* **@yesterday**: show the notes modified the day before the current
* **@lastXdays**: show the notes modified the last X days, replace X with any number.
* **@images**: shows the notes which contain images
* **@files**: shows the notes which contain files
* **@attachments**: shows the notes with files or images
* **@task**: shows the notes which include at least one todo element, either complete or not
* **@todo**: shows only the notes with not completed todos
* **@done**: shows only the notes with all the todos completed
* **@code**: shows the notes which includes at least one code snippet
* **@date**: show all the notes modified in a specific date, e.g. `@date(2018-09-05)`
* **@cdate**: show all the notes created in a specific date, e.g. `@cdate(2018-09-05)`
* Note that for @date and @cdate, there is no space between the command and first parenthesis
These Special Searches can be combined with any search term for more specific results. For example: `@images @todo “bear faq”` will search for all the notes that have images, uncompleted todos, and the exact phrase of `bear faq`.

Dates for `@cdate` and `@date` can be expressed in the ISO8061 format `@date(2018-12-23)` or according to your device’s local date format, for example `@date(23/12/2018)` in the U.S.A.

[Advanced search options in Bear - Bear - Faq and support](https://bear.app/faq/Advanced%20search%20options%20in%20Bear/)