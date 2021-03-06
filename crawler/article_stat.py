import os
import re
import sys
import glob
from collections import defaultdict
import pandas as pd
pd.set_option('display.max_columns', 999)
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
sys.path.append(".")
from utils.utils import read_article_urls, abbrev

urls_dir = "../processed_data/crawler/nejm/urls/"
in_dir = "../processed_data/crawler/nejm/articles/"
out_dir = "../processed_data/crawler/article_stat/"
os.makedirs(out_dir, exist_ok=True)

# Functions
def get_article_length(in_dir, article_urls, status):
	container = defaultdict(lambda: \
		{"time": None, 
		"zh": {"text": None, "len": None},
		"en": {"text": None, "len": None},
		"zh_m_en": None})

	for index, row in article_urls.iterrows():
		for lang in ["zh", "en"]:
			year = row["year"]
			month = row["month"]
			article_id = row["id"]
			fn = f"{in_dir}/{year}/{month:02}/{article_id}.{status}.{lang}"
			print(f"path: {fn}")

			try:
				with open(fn, "r") as f: text = f.readlines()
				length = len(text)
				container[article_id]["time"] = (int(year),int(month))
				container[article_id][lang]["text"] = text
				container[article_id][lang]["len"] = length

				if container[article_id]["zh"]["len"] != None and \
					container[article_id]["en"]["len"] != None:
					container[article_id]["zh_m_en"] = \
						container[article_id]["zh"]["len"] - \
						container[article_id]["en"]["len"]
			except:
				print("Article not found.")

	article_stat = []
	for i, (k, v) in enumerate(container.items()):
		article_stat.append(pd.DataFrame({"id": k, "year": \
			v["time"][0], "month": v["time"][1], \
			"zh_len": v["zh"]["len"], "en_len": v["en"]["len"], \
			"zh_m_en": v["zh_m_en"]}, index=[i]))
	article_stat = pd.concat(article_stat)
	article_stat["type_abbr"] = article_stat["id"].apply(lambda x: re.sub("[0-9%]+", "", x))
	article_stat["status"] = status
	try:
		article_stat["abs_diff"] = article_stat["zh_m_en"].apply(lambda x: abs(x))
	except TypeError:
		print("NaN found in zh_m_en.")
	return article_stat


def p1():
	# Make plot data:
	plot_data = pd.concat([full_articles, filt_articles])
	plot_data["type"] = plot_data["type_abbr"].apply(lambda x: abbrev[x])
	plot_data = plot_data.groupby(["type", "status"]).\
		agg(mean_diff=pd.NamedAgg("abs_diff", "mean")).reset_index()
	plot_data["Filter"] = plot_data["status"].\
		apply(lambda x: "Before" if x == "full" else "After")
	order = plot_data[plot_data["status"]=="full"].\
		sort_values("mean_diff", ascending=False)["type"].tolist()

	# Plot:
	fig, ax = plt.subplots(1,1)
	ax.clear()
	sns.barplot(x="type", y="mean_diff", hue="Filter", \
		data=plot_data, order=order)
	ax.spines['right'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.set_xticklabels(labels=plot_data["type"], rotation=90, linespacing=0.95)
	ax.set_xlabel(None)
	ax.set_ylabel("Mean Abs Diff in \n# of Paragraphs")
	fig.set_size_inches(5,3)
	fig.tight_layout()
	fig.savefig(f"{out_dir}/length_difference.pdf")

def p2():
	fig, (ax1, ax2) = plt.subplots(1,2)
	ax1.scatter(x="zh_len", y="en_len", data=full_articles)
	ax2.scatter(x="zh_len", y="en_len", data=filt_articles)
	xlim = ylim = ax1.get_ylim()
	ax1.plot(xlim, ylim, color="red", linestyle="dashed")
	xlim = ylim = ax2.get_ylim()
	ax2.plot(xlim, ylim, color="red", linestyle="dashed")
	fig.text(0.5, 0.01, "No. Chinese Paragraphs", ha="center")
	fig.text(0.0, 0.5, "No. English Paragraphs", va="center", rotation="vertical")
	ax1.set_title("Pre-filter")
	ax2.set_title("Post-filter")
	fig.set_size_inches(5,2.7)
	fig.tight_layout()
	fig.savefig(f"{out_dir}/length_comparison.pdf")


def p3():
	fig, ax = plt.subplots(1,1)
	ax.spines['right'].set_visible(False)
	ax.spines['top'].set_visible(False)
	ax.scatter(x="zh_len", y="en_len", data=full_articles, color="#7f7f7f")
	ax.scatter(x="zh_len", y="en_len", data=filt_articles, color="#1f77b4")
	xlim = ylim = ax.get_ylim()
	ax.plot(xlim, ylim, color="red", linestyle="dashed")
	ax.legend(labels=["Diagonal", "Pre-filter", "Post-filter"])
	ax.set_xlabel("No. Chinese Paragraphs")
	ax.set_ylabel("No. English Paragraphs")
	fig.set_size_inches(4,4)
	fig.tight_layout()
	fig.savefig(f"{out_dir}/length_comparison_overlay.pdf")


def main():
	# Read article and urls:
	article_urls = read_article_urls(urls_dir)
	article_urls = article_urls[article_urls["year"] != 2020] # Remove year 2020
	# 1973 articles

	full_articles = get_article_length(in_dir, article_urls, "full")
	filt_articles = get_article_length(in_dir, article_urls, "filt")
	full_articles["abs_diff"].describe()
	# count    1973.000000
	# mean       11.831221
	# std        19.538525
	# min         0.000000
	# 25%         1.000000
	# 50%         1.000000
	# 75%        19.000000
	# max       130.000000
	filt_articles["abs_diff"].describe()
	# count    1973.000000
	# mean        0.274709
	# std         0.638960
	# min         0.000000
	# 25%         0.000000
	# 50%         0.000000
	# 75%         0.000000
	# max         5.000000
	p1()
	p2()
	p3()
if __name__ == "__main__":
	main()
