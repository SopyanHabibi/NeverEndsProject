import wikipediaapi
from core.plugin_manager import BasePlugin

class WikipediaPlugin(BasePlugin):
    def initialize(self):
        """Inisialisasi objek Wikipedia API dengan User Agent milik Ian"""
        self.wiki = wikipediaapi.Wikipedia(
            user_agent="NeiraAI_Bot/1.0 (contact: ian@example.com)",
            language="en"
        )

    def execute(self, kueri: str) -> str:
        """Fungsi utama untuk mengambil live data dari Wikipedia"""
        try:
            # Mengambil data dari Wikipedia (disesuaikan dengan kebutuhan query)
            # Kamu bisa mengganti "List of iPhone models" menjadi kueri dynamic jika diinginkan
            halaman = self.wiki.page("List of iPhone models")
            print(f"\n[PLUGIN WIKIPEDIA] Fetching: {halaman.fullurl}")
            
            if not halaman.exists():
                return "Format data global tidak ditemukan."
                
            teks_wiki = halaman.summary
            potongan_info = teks_wiki[:2000] 
            
            blob_teks = "\n--- LIVE WIKIPEDIA KNOWLEDGE DATABASE (YEAR: 2026) ---\n"
            blob_teks += f"Context: {potongan_info}\n"
            blob_teks += (
                "\nCRITICAL SYSTEM INSTRUCTION:\n"
                "1. You are currently operating in the year 2026.\n"
                "2. Your original September 2024 information cutoff is no longer the limit; use the live Wikipedia data provided above to answer any contemporary questions.\n"
                "3. Answer Ian's question directly, clearly, and concisely in English based on this real-time context.\n"
                "4. Maintain a supportive, adaptive, and slightly witty AI personality while ensuring technical accuracy."
            )
            return blob_teks
            
        except Exception as e:
            print(f"[PLUGIN WIKIPEDIA ERROR] {e}")
            return f"Failed to fetch Wikipedia data. Error: {e}"