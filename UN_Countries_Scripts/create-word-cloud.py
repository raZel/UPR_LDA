import wordcloud
import argparse

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--frequency-file', required=True, help=f'path to frequency csv file')
	parser.add_argument('--image-file', required=True, help=f'path to save image file')
	parser.add_argument('--max-words', type=int, default=30, help=f'how many words to include in the cloud')
	

	args = parser.parse_args()
	freq_dict = {}
	with open(args.frequency_file) as f:
		lines = [line.rstrip() for line in f][:args.max_words]
		freq_dict = {line.split(',')[0]: float(line.split(',')[1]) for line in lines }
		wordcloud.WordCloud(
			mode="RGBA",
			background_color=None
		).fit_words(freq_dict).to_file(args.image_file)
	
		




