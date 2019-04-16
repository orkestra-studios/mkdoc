import markdown, re, os, hashlib
from time import sleep
from threading import Thread, Event
from argparse import ArgumentParser, Action

# regex formulas
block = re.compile(r'{%body%}')
code = re.compile(r'<p><code>(.*?)</code></p>',re.DOTALL)
# embed a section after each header
h1 = re.compile(r'</h1>(.*?)(<h1>|</body>)',re.DOTALL)
h2 = re.compile(r'</h2>(.*?)(<h2>|<h1>|</body>)',re.DOTALL)
h3 = re.compile(r'</h3>(.*?)(<h3>|<h2>|<h1>|</body>)',re.DOTALL)
h4 = re.compile(r'</h4>(.*?)(<h4>|<h3>|<h2>|<h1>|</body>)',re.DOTALL)
h5 = re.compile(r'</h5>(.*?)(<h5>|<h4>|<h3>|<h2>|<h1>|</body>)',re.DOTALL)
h6 = re.compile(r'</h6>(.*?)(<h6>|<h5>|<h4>|<h3>|<h2>|<h1>|</body>)',re.DOTALL)

def filehash(fn):
    BUFSIZE = 4096
    sha1 = hashlib.sha1()
    with open(fn, 'rb') as f:
        chunk = f.read(BUFSIZE)
        while len(chunk) > 0:
            sha1.update(chunk)
            chunk = f.read(BUFSIZE)
    return sha1.hexdigest()

def watch(shutdown, template, infile, outfile): 

    last_update = os.stat(infile).st_mtime
    last_hash = filehash(infile)
    while not shutdown.isSet(): 
        try:
            # first, check if the file is saved
            updated = os.stat(infile).st_mtime 
            assert updated > last_update, "no save detected."
            last_update = updated
            # then check for changes
            new_hash = filehash(infile)
            assert last_hash != new_hash, "no changes detected."
            last_hash = new_hash
            # should generate document
            print("generating html...")
            #get base text
            text = "Nebuu API Docs"
            with open(infile) as f:
                text = f.read()
            make(text, template, outfile)
        except AssertionError as e: pass #print(e)
        except Exception as e: print(e)
        finally: sleep(1)
    print("stopped watcher")

def make(text, template, outfile):
    #markdown
    md = markdown.Markdown()
    body = md.convert(text)

    #wrap template
    wrapped = block.sub(body, template)

    #create sections
    restructured = h1.sub(r"</h1>\n<section>\n\1\n</section>\n\2",
                   h2.sub(r"</h2>\n<section>\n\1\n</section>\n\2",
                   h3.sub(r"</h3>\n<section>\n\1\n</section>\n\2",
                   h4.sub(r"</h4>\n<section>\n\1\n</section>\n\2",
                   h5.sub(r"</h5>\n<section>\n\1\n</section>\n\2",
                   h6.sub(r"</h6>\n<section>\n\1\n</section>\n\2",
                   code.sub(r"<pre><code>\1</code></pre>",
                   wrapped                                 )))))))

    #create html
    with open(outfile, "w") as f:
        f.write(restructured)

def getArgs():
    parser = ArgumentParser(description="Generate beautified HTML from markdown text.")
    parser.add_argument("input", help="path to markdown file.")
    parser.add_argument("-t", "--template", metavar="TEMPLATE", default="template.html", help="path to template file. default: template.html")
    parser.add_argument("-o", "--output", metavar="OUTFILE", default=None, help="path to output file. default: <input name>.html")
    parser.add_argument("-w", "--watch", action='store_true', help="watch the file for changes.")
    return parser.parse_args()

def get_template(fn):
    template = "{%body%}"
    with open(fn) as f:
        template = f.read()
    return template

if __name__ == "__main__":
    args = getArgs()
    shutdown = Event()
    template = get_template(args.template)
    if args.output:
        output = args.output
    else:
        output = args.input.rsplit(".")[0] + ".html"
    if args.watch:
        print("watching: {}".format(args.input))
        t = Thread(target=watch, args=(shutdown, template, args.input, output))
        t.start()
        try:
            while True: sleep(10)
        except KeyboardInterrupt:
            print("\nexiting.")
            shutdown.set()
        finally: t.join()
    else:
        text = "Nebuu API Docs"
        with open(args.input) as f:
            text = f.read()
        make(text, template, output)
