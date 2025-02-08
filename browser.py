import tkinter
import tkinter.font
import ssl
import socket

WIDTH, HEIGHT = 800, 600  # Size of the srcreen

SCROLL_STEP = 100

HSTEP, VSTEP = 13, 18


class Text:
    """This class is used to create a text object to be added to the `out` list in the `lex` function."""

    def __init__(self, text):
        self.text = text


class Tag:
    """This class is used to create a text object to be added to the `out` list in the `lex` function."""

    def __init__(self, tag):
        self.tag = tag


class Layout:

    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"

        for tok in tokens:
            self.token(tok)

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"

    def word(self, word):
        font = tkinter.font.Font(
            size=16,
            weight=self.weight,
            slant=self.style
        )
        w = font.measure(word)
        self.display_list.append(
            (self.cursor_x,  self.cursor_y, word, font))
        self.cursor_x += w + font.measure(" ")
        if self.cursor_x + w >= WIDTH - HSTEP:
            self.cursor_y += font.metrics("linespace") * 1.25
            self.cursor_x = HSTEP


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window,
                                     width=WIDTH,
                                     height=HEIGHT)
        self.canvas.pack()

        self.scroll = 0

        self.window.bind("<Down>", self.scrolldown)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def load(self, url):
        body = url.request()
        tokens = lex(body)  # tokens is a list of tag and text objects
        # create a layout object initialized with tokens and access
        # the display_list fields
        self.display_list = Layout(tokens).display_list
        self.draw()

    def draw(self):

        self.canvas.delete("all")
        for x, y, c, font in self.display_list:
            if y > self.scroll+HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(
                x, y-self.scroll, text=c, anchor='nw', font=font)


class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/"not in url:
            url += "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

# Requesting a website

    def request(self):

        s = socket.socket(family=socket.AF_INET,
                          type=socket.SOCK_STREAM,
                          proto=socket.IPPROTO_TCP,)
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "\r\n"
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read()
        s.close()
        return content


def lex(body):
    """
    This function creates a list of output that contains the address of the tags and texts of the html body

    Parameters:
    body (): The HTML body content

    Returns:
    out: The list of html content as either a Tag or a Text object
    """
    out = []
    buffer = ""
    in_tag = False

    for c in body:
        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
