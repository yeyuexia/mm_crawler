import sys
import os
import getopt

import crawler

OPTIONS = "hs:n:o:l:"
LONG_OPTIONS = []

def usage():
    print """ this file is used for crawler images from target link
    -h print help.
    -n set the number of crawler worker, defaults 10
    -l set the capicity of images download, defaults infinity.
    -0 set the output dir for images, defaults pics
    """

def run():
    try:
        optlist, args = getopt.getopt(sys.argv[1:], OPTIONS, LONG_OPTIONS)
    except getopt.GetoptError as e:
        print str(e)
        sys.exit(2)
    thread_num = 10
    output_path = "pics"
    capicity = -1
    begin_url = "22mm.cc"
    print optlist
    for option, value in optlist:
        if option == "-h":
            usage()
            sys.exit()
        elif option == "-n":
            try:
                thread_num = int(value)
            except Exception as e:
                print "command error"
                usage()
                sys.exit(2)
        elif option == "-o":
            output_path = value
        elif option == "-l":
            try:
                capicity = int(value)
            except Exception as e:
                print "command error"
                usage()
                sys.exit(2)
        elif option == "-s":
            begin_url = value
    try:
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
    except Exception as e:
        print "invalid path"
        sys.exit(2)
    if not begin_url.startswith("http://"):
        begin_url = "http://" + begin_url
    crawler.run(begin_url, capicity, output_path, thread_num)

if __name__ == "__main__":
    run()
