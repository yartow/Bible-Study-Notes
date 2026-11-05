# Tutorial on Regular Expressoins
#it/tutorial/regex
#biblestudy/devotionals/nehemiah 
## Finding specific string 
This example `**[^29]**` can be found with the following string

```regex
\*\*\[\^(\d+)\]\*{2}
```

and `[^a]` or `[^6]` could be found with 

```regex
\[\^(\w+)\]
```
with 
* `\*{2}` two consecutive asterisks
* `()` a group
* `\d+` multiple digits
* `\d` - een nummer (`0-9`)
* `\w` - een woord (`a-z` en `0-9` en `_`)
* `\s` - whitespace (tab, spatie, line breaks)
* ` .`- elk karakter
* `*` - 0 of meer
* `+` - 1 of meer
* `{5}` - exact 5 keer
* `\` - escape voor speciale karakters als `\, *, (){}[]`, etc
* `\D`, `\W`, `\S` - géén nummer, woord of whitespace
* `[abc123]` - a, b, c, 1, 2 òf 3
* `[a-z0-9]` - a, b, c, 1, 2 òf 3
* `^`, `$` - begin en einde van de regel, e.g. 

### Anchors
Anchors do not match any characters. They match a position. `^` matches at the start of the string, and `$` matches at the end of the string. Most regex engines have a “multi-line” mode that makes `^` match after any line break, and `$` before any line break. E.g. `^b` matches only the first *b* in bob.

https://www.regular-expressions.info/quickstart.html

#todo/nogaftemaken 

## Replacing specific string
The *n*th result is stored in `\[n]`. So in the *Replace* field in a text editor such as Sublime, `\1` would return the first occurence of that which is found and the whole string would be replaced by this. 