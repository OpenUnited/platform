from apps.capabilities.product_management.services import ProductService


def test_convert_youtube_link_to_embed(video_link, embed_video_link):
    assert ProductService.convert_youtube_link_to_embed("") is None
    assert ProductService.convert_youtube_link_to_embed(video_link) == embed_video_link
