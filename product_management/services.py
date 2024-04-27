class ProductService:
    @staticmethod
    def convert_youtube_link_to_embed(url: str):
        if url:
            return url.replace("watch?v=", "embed/")
