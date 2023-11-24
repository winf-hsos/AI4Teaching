from bluechat import Assistant
from bluechat import log

class VideoAssistant(Assistant):
    def __init__(self, config_file, depending_on_assistant=None):
        log("Initializing VideoAssistant")
        log(f"VideoAssistant depends on {depending_on_assistant}") if depending_on_assistant else None
        super().__init__(config_file, depending_on_assistant)

    def add_video(self, yotube_url):
        self.knowledge_base.add_youtube_video(yotube_url)

    def get_videos(self):
        return self.knowledge_base.get_documents_by_type("video/youtube")

    def lookup_videos_for_topic(self, topic, n_results=3):

        # TODO: Filter on videos only via metadata (should be taken care of by video assistant)
        retrieved_documents = self.vector_db.query(topic, n_results=n_results)

        if len(retrieved_documents["ids"][0]) == 0:
            log(f"No videos found for topic >{topic}<")
            return None

        metdata = retrieved_documents["metadatas"][0]

        # Create the youtube links
        youtube_links = self._create_youtube_links(retrieved_documents)

        # Lookup the summary for each segment
        chunk_ids = retrieved_documents["ids"][0]
        summaries = self._lookup_summaries(chunk_ids)

        return [{ "youtube_link" : yt_link, "summary" : summaries[i], "start" : metdata[i]["start"], "end" : metdata[i]["end"] } for i, yt_link in enumerate(youtube_links)]
    
    def _create_youtube_links(self, retrieved_document):
        youtube_links = []
        for metadata in retrieved_document["metadatas"][0]:
            link = f"https://www.youtube.com/watch?v={metadata['youtube_id']}&t={round(metadata['start'])}"
            youtube_links.append(link)

        return youtube_links
    
    def _lookup_summaries(self, chunk_ids):
        summaries = []
        for chunk_id in chunk_ids:
            summary = self.knowledge_base.get_summary_for_chunk_id(chunk_id)
            summaries.append(summary)
        return summaries
    