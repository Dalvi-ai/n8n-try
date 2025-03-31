import os
import time
import requests
import subprocess
from datetime import datetime

# Configurações
OUTPUT_DIR = "outputs"
SCRIPT_DIR = os.path.join(OUTPUT_DIR, "scripts")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
VIDEO_DIR = os.path.join(OUTPUT_DIR, "video")
FINAL_DIR = os.path.join(OUTPUT_DIR, "final")

# Certifique-se de que os diretórios de saída existam
for directory in [SCRIPT_DIR, AUDIO_DIR, VIDEO_DIR, FINAL_DIR]:
    os.makedirs(directory, exist_ok=True)

class VideoProductionAgent:
    def _init_(self, openai_api_key, replicate_api_key):
        """
        Inicializa o agente de produção de vídeos.
        
        Args:
            openai_api_key (str): Chave de API para OpenAI
            replicate_api_key (str): Chave de API para Replicate
        """
        self.openai_api_key = openai_api_key
        self.replicate_api_key = replicate_api_key
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_script(self, prompt):
        """
        Gera um script baseado no prompt fornecido.
        
        Args:
            prompt (str): Prompt descrevendo o vídeo desejado
            
        Returns:
            str: Script gerado
        """
        print("🔄 Gerando script...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        system_prompt = """
        Você é um roteirista profissional especializado em criar scripts para vídeos.
        Você deve criar um script completo, claro e envolvente.
        O script deve incluir todas as falas, ser dividido por seções (Introdução, Desenvolvimento, Conclusão)
        e ter entre 300-500 palavras para um vídeo de 2-3 minutos.
        Use uma linguagem natural, conversacional e um tom profissional mas acessível.
        """
        
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Erro ao gerar script: {response.text}")
        
        script = response.json()["choices"][0]["message"]["content"]
        
        # Salvar script
        script_filename = f"script_{self.timestamp}.txt"
        script_path = os.path.join(SCRIPT_DIR, script_filename)
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
            
        print(f"✅ Script gerado e salvo em: {script_path}")
        return script, script_path
    
    def generate_audio(self, script):
        """
        Converte o script em áudio usando a API do Replicate.
        
        Args:
            script (str): Texto do script
            
        Returns:
            str: Caminho para o arquivo de áudio gerado
        """
        print("🔄 Gerando áudio a partir do script...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.replicate_api_key}"
        }
        
        # Modelo Replicate para TTS - usando bark ou outro modelo adequado
        data = {
            "version": "ad76a56df6703904d3d2021a0ac213e8a714c493b5326546cd8ecf005fe74e22",  # Modelo bark
            "input": {
                "text": script,
                "speaker": "en_speaker_9",  # Pode ajustar conforme necessário
                "language": "pt",           # Pode mudar conforme necessidade
                "preset": "balanced"
            }
        }
        
        # Iniciar a geração
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 201:
            raise Exception(f"Erro ao iniciar geração de áudio: {response.text}")
        
        prediction = response.json()
        prediction_id = prediction["id"]
        
        # Verificar status até a conclusão
        while True:
            response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {self.replicate_api_key}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro ao verificar status de áudio: {response.text}")
            
            prediction = response.json()
            
            if prediction["status"] == "succeeded":
                audio_url = prediction["output"]
                break
            elif prediction["status"] == "failed":
                raise Exception("Falha na geração de áudio")
            
            print("⏳ Aguardando geração de áudio...")
            time.sleep(5)
        
        # Baixar o áudio
        audio_filename = f"audio_{self.timestamp}.mp3"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        
        audio_response = requests.get(audio_url)
        if audio_response.status_code != 200:
            raise Exception("Erro ao baixar o áudio")
        
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)
            
        print(f"✅ Áudio gerado e salvo em: {audio_path}")
        return audio_path
    
    def generate_video(self, script):
        """
        Gera um vídeo baseado no script usando a API do Replicate.
        
        Args:
            script (str): Texto do script para guiar a geração visual
            
        Returns:
            str: Caminho para o arquivo de vídeo gerado
        """
        print("🔄 Gerando vídeo baseado no script...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.replicate_api_key}"
        }
        
        # Modelo para geração de vídeo - usando stable-video-diffusion ou outro modelo adequado
        data = {
            "version": "a4a8bafd6089e5156a83b4b3b3a80cb615ddc4b643b92727abf9c59d5541d3e2",  # stable-video-diffusion
            "input": {
                "prompt": script, 
                "negative_prompt": "Poor quality, blurry, distorted, unrealistic",
                "width": 1024,
                "height": 576,
                "num_outputs": 1,
                "num_inference_steps": 50,
                "guidance_scale": 7.5
            }
        }
        
        # Iniciar a geração
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 201:
            raise Exception(f"Erro ao iniciar geração de vídeo: {response.text}")
        
        prediction = response.json()
        prediction_id = prediction["id"]
        
        # Verificar status até a conclusão
        while True:
            response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {self.replicate_api_key}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro ao verificar status de vídeo: {response.text}")
            
            prediction = response.json()
            
            if prediction["status"] == "succeeded":
                video_url = prediction["output"][0]  # Primeiro output é o vídeo
                break
            elif prediction["status"] == "failed":
                raise Exception("Falha na geração de vídeo")
            
            print("⏳ Aguardando geração de vídeo...")
            time.sleep(10)  # Vídeos geralmente demoram mais
        
        # Baixar o vídeo
        video_filename = f"video_sem_audio_{self.timestamp}.mp4"
        video_path = os.path.join(VIDEO_DIR, video_filename)
        
        video_response = requests.get(video_url)
        if video_response.status_code != 200:
            raise Exception("Erro ao baixar o vídeo")
        
        with open(video_path, "wb") as f:
            f.write(video_response.content)
            
        print(f"✅ Vídeo gerado e salvo em: {video_path}")
        return video_path
    
    def merge_audio_video(self, video_path, audio_path):
        """
        Combina o vídeo e o áudio usando FFmpeg.
        
        Args:
            video_path (str): Caminho para o arquivo de vídeo
            audio_path (str): Caminho para o arquivo de áudio
            
        Returns:
            str: Caminho para o vídeo final
        """
        print("🔄 Mesclando áudio e vídeo...")
        
        final_filename = f"video_final_{self.timestamp}.mp4"
        final_path = os.path.join(FINAL_DIR, final_filename)
        
        try:
            # Comando FFmpeg para mesclar áudio e vídeo
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",      # Manter codec de vídeo
                "-c:a", "aac",       # Codec de áudio
                "-map", "0:v:0",     # Manter faixa de vídeo do primeiro arquivo
                "-map", "1:a:0",     # Usar faixa de áudio do segundo arquivo
                "-shortest",         # Usar a duração do arquivo mais curto
                final_path
            ]
            
            # Executar comando
            subprocess.run(cmd, check=True)
            
            print(f"✅ Vídeo final com áudio salvo em: {final_path}")
            return final_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro ao mesclar áudio e vídeo: {e}")
    
    def create_video(self, prompt):
        """
        Executa o fluxo completo de criação de vídeo.
        
        Args:
            prompt (str): Prompt descrevendo o vídeo desejado
            
        Returns:
            dict: Informações sobre os arquivos gerados
        """
        try:
            # 1. Gerar script
            script, script_path = self.generate_script(prompt)
            
            # 2. Gerar áudio a partir do script
            audio_path = self.generate_audio(script)
            
            # 3. Gerar vídeo baseado no script
            video_path = self.generate_video(script)
            
            # 4. Mesclar áudio e vídeo
            final_video_path = self.merge_audio_video(video_path, audio_path)
            
            # 5. Retornar informações
            return {
                "status": "success",
                "message": "Vídeo criado com sucesso!",
                "files": {
                    "script": script_path,
                    "audio": audio_path,
                    "video_sem_audio": video_path,
                    "video_final": final_video_path
                },
                "script_preview": script[:200] + "..." if len(script) > 200 else script
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# Exemplo de uso do agente
def start_agent():
    # Obter as chaves de API do ambiente ou configurá-las diretamente
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    replicate_api_key = os.environ.get("REPLICATE_API_KEY")
    
    if not openai_api_key or not replicate_api_key:
        print("⚠️ As chaves de API não estão configuradas. Por favor, defina as variáveis de ambiente OPENAI_API_KEY e REPLICATE_API_KEY.")
        return
    
    # Inicializar o agente
    agent = VideoProductionAgent(openai_api_key, replicate_api_key)
    
    # Receber o prompt do usuário
    print("🤖 Agente de Produção de Vídeos com IA")
    print("---------------------------------------")
    prompt = input("Descreva o vídeo que você deseja criar: ")
    
    # Executar o processo
    print("\n🚀 Iniciando produção de vídeo...\n")
    result = agent.create_video(prompt)
    
    # Mostrar resultados
    if result["status"] == "success":
        print("\n✨ Produção de vídeo concluída com sucesso!")
        print("\nPreview do script:")
        print("-----------------")
        print(result["script_preview"])
        print("\nArquivos gerados:")
        for file_type, file_path in result["files"].items():
            print(f"- {file_type}: {file_path}")
    else:
        print(f"\n❌ Erro: {result['message']}")


if __name__ == "__main__":
    start_agent()