import os
from collections.abc import AsyncGenerator

import google.generativeai as genai
from litestar import Litestar, Request, get
from litestar.enums import MediaType
from litestar.exceptions import ClientException
from litestar.response import Response, Stream

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
assert GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


@get("/favicon.ico")
async def favicon() -> Response:
    return Response(content="", status_code=404)


@get(["/", "/{path:path}"])
async def gen_page_route(request: Request) -> Stream:
    content_type = request.headers.get("Accept", "")
    media_type = None
    if "text/html" in content_type:
        media_type = MediaType.HTML
    if "text/plain" in content_type:
        media_type = MediaType.TEXT
    if request.url.path.endswith(".html"):
        media_type = MediaType.HTML
    if request.url.path.endswith(".txt"):
        media_type = MediaType.TEXT

    if media_type is None:
        raise ClientException(
            detail="Unsupported Media Type",
        )

    async def generate_html_stream() -> AsyncGenerator[bytes, None]:
        prompt = f"""\
You are an HTTP server simulating dynamic page generation.
Method: {request.method}, Path: {request.url}
Respond in {media_type.value} format only.
Do not use any markdown code blocks (```) in your output.

For plain text: Just provide relevant content.

For HTML:
 - Include <meta charset='utf-8'>
 - Use inline styles only
 - Do not link to local resources (images, CSS, JS)
 - It's okay to use external resources or public APIs
 - Include at least one hyperlink
 - Content should use slug-style URLs
"""

        response = await model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            yield chunk.text.encode()

    return Stream(content=generate_html_stream(), media_type=media_type)


app = Litestar(
    [favicon, gen_page_route],
)
