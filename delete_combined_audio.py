import os

# Direktori tempat file audio disimpan
directory = "D:\Tugas\TalkEnglish"

# Loop untuk mencari dan menghapus file dengan awalan 'combined_output_'
for filename in os.listdir(directory):
    if filename.startswith("combined_output_"):
        file_path = os.path.join(directory, filename)
        try:
            os.remove(file_path)
            print(f"File {filename} telah dihapus.")
        except Exception as e:
            print(f"Error saat menghapus {filename}: {e}")

# Loop untuk mencari dan menghapus file dengan awalan 'combined_output_'
for filename in os.listdir(directory):
    if filename.startswith("test_output_en_"):
        file_path = os.path.join(directory, filename)
        try:
            os.remove(file_path)
            print(f"File {filename} telah dihapus.")
        except Exception as e:
            print(f"Error saat menghapus {filename}: {e}")

# Loop untuk mencari dan menghapus file dengan awalan 'combined_output_'
for filename in os.listdir(directory):
    if filename.startswith("test_output_id_"):
        file_path = os.path.join(directory, filename)
        try:
            os.remove(file_path)
            print(f"File {filename} telah dihapus.")
        except Exception as e:
            print(f"Error saat menghapus {filename}: {e}")
