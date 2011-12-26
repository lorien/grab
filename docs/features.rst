.. _overview:

Grab features
=============

Overview of Grab interface
--------------------------

 * Simple API
 * Session suppport (automated cookie processing)
 * Building HTTP request of any type
 * Multipart POST (with easy API for file uploading)
 * Form processing
 * Selecting HTML elements via XPath/CSS queries
 * Ability to choose network layer: curl, urllib, selenium (only curl transport is stable)
 * Proxy support: http, socks, authorization.
 * Default HTTP headers similar to real browser
 * Random User-Agent which is choosed from list of real browser user-agents.
 * Proxy list interface
 * Framework to develop well-structured site scrapers
 * Different utilities to debug scraping process
 * Ability to disable download the body of response or limit the downloading
   part of response body.
 * Automatic detection of response body charset
 * Ability to set connect timeout and overall timeout for the request
 * Hammer mode: multiple tries in case of network errors


Overview of Spider interface
----------------------------

 * Consistent way to write your site scrapers
 * Asynchronous (multicurl)
 * Cache support
 * Verbose statistics about parsing process
