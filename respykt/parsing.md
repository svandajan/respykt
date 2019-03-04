# Parsing *Respekt* Web Pages

Parsing is done by BeautifulSoap4, mainly using functions `find_all` and `find`,
called from current tag (e.g. `items = html.find_all(class_="issuedetail-categorized-item")`
for getting list of all articles). Because the function `[tag].find_all(...)` is so heavily 
used, it could be shortcutted to just `[tag](...)` (e.g. `items = html(class_="issuedetail-categorized-item")`
from the previous example). 

### Search for issue URL on homepage

Page URL: `https://www.respekt.cz/`, feeded to BeautifulSoup and stored in `home`

* URL of current issue
    * `home.find(class_="currentissue").a["href"]`
* Post data for loging in
    * `"username": {username}` 
    * `"password": {password}`
    * `"do": "authBox-loginForm-submit"` 
    * `"_do": "authBox-loginForm-submit"`

### Parsing current issue page

Page URL: `https://www.respekt.cz/tydenik/{year}/{issue_no}`, stored in `html`

* URL of issue cover
    * `html.find(class_="heroissue").a["href"]`
    * Very large (width=2048px)
* Issue title
    * `html.find(class_="heroissue").h2.text`
* Issue subtitle - issue theme
    * `html.find(class_="heroissue").find("div", class_="heroissue-theme").text`
* Issue date
    * `html.find(class_="heroissue").find("time", class_="heroissue-date").text`
    * Format: `{issue_no}/{year}, {day_from}. {month_from}.? {year_from}? ?- ?{day_to}. {month_to}. {year_to}`
    * Example: *51/2002, 16.–23. 12. 2002*
    * Example: *9/2019, 25. 2. – 3. 3. 2019*
* TOC
    * `html.find(class_="issuedetail-categorized")`
* Categories
    * `categories = html(class_="issuedetail-categorized-sectionname")`
* Items
    * `items = html(class_="issuedetail-categorized-item")`
    * **!!** are not nested in categories, but tag containing category is one of *previous siblings* of article tag
    * Category: `items[{}].find_previous_sibling(class_="issuedetail-categorized-sectionname").text.strip()`
    * URL: `items[{}]["href"]`
    * Title: `items[{}].find(class_="issuedetail-categorized-title").text.strip()`
    * Author: `items[{}].find(class_="issuedetail-categorized-author").text.strip()`
    * Perex: `items[{}].find(class_="issuedetail-categorized-perex").text.strip()`
    * Lock: `items[{}].find(class_="lock")` - indicates, that you have to have active subscription to 
    read this article (otherwise, you will get only three paragraphs)
    
### Navigating the article

Article URL (grabbed from index page): `https://www.respekt.cz/tydenik/2019/9/kdyby-tisic-malacovych?issueId=100388`, 
stored in `art`

* Topics
    * `art.find(class_="post-topics").find_all("a")`
    * The second one is usually a Category
* Title
    * `art.find("h1",class_="post-title")`
* Subtitle
    * `art.find("h2",class_="post-subtitle")`
* Header Image
    * `art.find("header",class_="post-header").find("figure", class_="frame")`
    * have multiple sizes, defined in `<source>` tag and `srcset` attribute with multiple entries - `art.find("figure", class_="frame").source["srcset"]`: 
        * https://respekt.mgwdata.net/5z89cf/adb4401f19ff060f3e6c58c8a656f94e.webp 120w, 
        * https://respekt.mgwdata.net/g6060w/d6ead2edc3f7cdfc475290b1e455d147.webp 150w, 
        * https://respekt.mgwdata.net/ebb02g/e3b40e06f03f68e510608cf3bcf880f5.webp 201w, 
        * https://respekt.mgwdata.net/7mh2y4/129537491b07fc099e8e58a5426259f2.webp 320w, 
        * https://respekt.mgwdata.net/3dbk91/c158e54ccd2fa4f5772fae1872d503f3.webp 480w, 
        * https://respekt.mgwdata.net/6ftugz/c88d8c1ba919984d7e75ba463fe9bf26.webp 760w*
* Authors
    * `art.find(class_="authorship-names")`
* Date of publication
    * `art.find(class_="authorship-note")`
* Content
    * `art.find(id="postcontent")`