from Retriever import Retriever


def main():
    retriever = Retriever()
    while True:
        query = input("Enter query: ")
        topk = int(input("Enter topk: "))
        metadata_filter = {}
        results = retriever.query(
            query=query, topk=topk, metadata_filter=metadata_filter
        )
        print(results)


if __name__ == "__main__":
    main()
