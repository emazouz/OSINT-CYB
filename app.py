from flack import Flack , render_template , request , jsonify
from playwright.sync_api import sync_playwright
app = Flack(__name__);



def classify_site(link, title): 
    link_lower = link.lower() if link else ""
    title_lower = title.lower() if title else ""
    

    # Define a mapping of social media platforms to their identifying keywords


    social_sites = {
        "facebook": ["facebook.com", "fb.com", "facebook", "fb", "meta", "meta.com", "meta platforms", "meta platforms inc", "meta platforms inc."],
        "twitter": ["twitter.com", "twitter", "x.com", "x", "x corp", "x corp.", "x corporation", "x corporation."],
        "linkedin": ["linkedin.com", "linkedin", "linkedin corporation", "linkedin corporation."],
        "instagram": ["instagram.com", "instagram", "insta", "insta.com"],
        "github": ["github.com", "github", "git hub", "git hub.com"],
        "youtube": ["youtube.com", "youtube", "yt.com", "yt", "youtube inc", "youtube inc.", "youtube corporation", "youtube corporation.", "youtu.be"],
        "tiktok": ["tiktok.com", "tiktok", "tt.com", "tt"],
        "whatsapp": ["whatsapp.com", "whatsapp", "wa.com", "wa"],
        "snapchat": ["snapchat.com", "snapchat", "snap.com", "snap"],
        "Telegram": ["telegram.org", "telegram.com", "telegram", "tg.com", "tg", "t.me"],
        "Google": ["google.com", "google", "goog", "goog.com", "google inc", "google inc.", "google corporation", "google corporation."],
        "Email": ["email", "mail", "e-mail", "e mail", "email.com", "mail.com"],
    }

    for site, keywords in social_sites.items():
        for keyword in keywords:
            if keyword in link_lower or keyword in title_lower:
                return site

    #  Define a mapping of educational platforms to their identifying keywords
    
    education_sites = {
        "Coursera": ["coursera.org", "coursera", "coursera.com"],
        "edX": ["edx.org", "edx", "edx.com"],
        "Udemy": ["udemy.com", "udemy"],
        "Khan Academy": ["khanacademy.org", "khan academy", "khanacademy"],
        "LinkedIn Learning": ["linkedin.com/learning", "linkedin learning", "linkedin-learning"],
        "Codecademy": ["codecademy.com", "codecademy"],
        "Pluralsight": ["pluralsight.com", "pluralsight"],
        "Udacity": ["udacity.com", "udacity"],
        "FutureLearn": ["futurelearn.com", "futurelearn"],
        "Skillshare": ["skillshare.com", "skillshare"],
    }

    for site, keywords in education_sites.items():
        for keyword in keywords:
            if keyword in link_lower or keyword in title_lower:
                return site

    # Define a mapping of news platforms to their identifying keywords

    news_sites = {
        "CNN": ["cnn.com", "cnn"],
        "BBC": ["bbc.com", "bbc"],
        "The New York Times": ["nytimes.com", "new york times", "ny times"],
        "The Guardian": ["theguardian.com", "guardian"],
        "Reuters": ["reuters.com", "reuters"],
        "Al Jazeera": ["aljazeera.com", "al jazeera"],
        "Fox News": ["foxnews.com", "fox news", "fox"],
        "NBC News": ["nbcnews.com", "nbc news", "nbc"],
        "CBS News": ["cbsnews.com", "cbs news", "cbs"],
        "The Washington Post": ["washingtonpost.com", "washington post", "wash post"],
    }

    for site, keywords in news_sites.items():
        for keyword in keywords:
            if keyword in link_lower or keyword in title_lower:
                return "News " + site
    
    # Check for email-related keywords in the title
    if any(email_word in title_lower for email_word in ["email", "mail", "e-mail", "e mail", "email.com", "mail.com", "@"]):
        return "Emails"

    # Check for phone-related keywords in the title
    if any(phone_word in title_lower for phone_word in ["phone", "call", "contact", "mobile", "cell", "tel", "telephone", "phone.com", "call.com", "contact.com", "mobile.com", "cell.com", "tel.com", "telephone.com", "+212", "رقم الهاتف", "اتصل", "هاتف", "جوال", "موبايل", "هاتف محمول", "رقم الجوال", "رقم الهاتف المحمول", ]):
        return "Phone Numbers"

    # Check for official website keywords in the link and title
    official_sites = [".gov", ".edu", ".org", "official", "official website", "official site", "official page", "official account", "official profile", "official page", "official profile", "official account", "official website", "official site", "official page", "official profile", "official account", "official website", "official site", "official page", "official profile", "official account"]

    for keyword in official_sites:
        if keyword in link_lower or keyword in title_lower:
            return "Official Website"
        

    
    general_sites = ["github.com", "github", "git hub", "git hub.com", "google.com", "google", "goog", "goog.com", "google inc", "google inc.", "google corporation", "google corporation.", ".com", ".net", ".org", ".io", ".co", ".us", ".uk", ".ca", ".de", ".fr", ".jp", ".cn", ".ru", ".br", ".in", ".au", ".eu", ".za", ".mx", ".es", ".it", ".nl", ".se", ".no", ".fi", ".dk", ".ch", ".at", ".be", ".pl", ".cz", ".gr", ".hu", ".ro", ".sk", ".bg", ".lt", ".lv", ".ee",".me", ".tv", ".cc", ".ws"]

    for keyword in general_sites:
        if keyword in link_lower or keyword in title_lower:
            return "General Website"


    return "websites"    
  



def osint_ex(query):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            search_link = f"https://duckduckgo.com/search?q={query}&t=h_&ia=web"
            page.goto(search_link, timeout=60000, wait_until="load")
            num_pages = 3
            all_results = []
            for _ in range(num_pages):
                page.wait_for_selector("article[data-testid='result']", timeout=60000)
                results = page.query_selector_all("article[data-testid='result'] a.result__a")
                for result in results:
                    try: 
                      title_element = result.query_selector("h2 a")
                      link_element = result.query_selector("h2 a")
                      image_element = result.query_selector("img")
                      if title_element and link_element:
                          title = title_element.inner_text().strip()
                          link = link_element.get_attribute("href").strip()
                          image = image_element.get_attribute("src").strip() if image_element else None
                          site_type = classify_site(link, title)
                          all_results.append({"title": title, "link": link, "image": image , "type": site_type})
                    except Exception:
                        continue

                          
                next_button = page.query_selector("button#more-results")
                if next_button:
                    next_button.click()
                    page.wait_for_load_state("load", timeout=4000)
                else:
                    break
            browser.close()
            return all_results    
    except Exception as e:
        print(f"Error during OSINT extraction: {e}")
        return []


@app.route("/")
def index():    
    return render_template("index.html")



@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")
    if not query:
        return jsonify({"error": "Query is required"}), 400
    results = osint_ex(query)
    return jsonify(results)




if __name__ == "__main__":
    app.run(debug=False, use_reloader=False);