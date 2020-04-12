from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from PIL import Image
import httpx
import pyheif
import io


async def homepage(request):
    url = request.query_params.get("url")
    if not url:
        return JSONResponse({"error": "?url= is required"})
    async with httpx.AsyncClient(verify=False) as client:
        image_response = await client.get(url)
    if image_response.status_code != 200:
        return JSONResponse(
            {
                "error": "Status code not 200",
                "status_code": image_response.status_code,
                "body": repr(image_response.content),
            }
        )
    heic = pyheif.read_heif(image_response.content)
    image = Image.frombytes(mode=heic.mode, size=heic.size, data=heic.data)
    # Resize based on ?w= and ?h=, if set
    width, height = image.size
    w = request.query_params.get("w")
    h = request.query_params.get("h")
    if w is not None or h is not None:
        if h is None:
            # Set h based on w
            w = int(w)
            h = int((float(height) / width) * w)
        elif w is None:
            h = int(h)
            # Set w based on h
            w = int((float(width) / height) * h)
        w = int(w)
        h = int(h)
        image.thumbnail((w, h))

    # ?bw= converts to black and white
    if request.query_params.get("bw"):
        image = image.convert("L")

    jpeg = io.BytesIO()
    image.save(jpeg, "JPEG")
    return Response(
        jpeg.getvalue(),
        media_type="image/jpeg",
        headers={"cache-control": "s-maxage={}, public".format(365 * 24 * 60 * 60)},
    )


app = Starlette(debug=True, routes=[Route("/", homepage),])
