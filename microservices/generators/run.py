import argparse

from info_extractor import (
    doc_string_generator,
    library_doc_generator,
    raw_code_extractor,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run file information extraction generators"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--doc-string",
        action="store_true",
        default=False,
        help="Doc string info generator",
    )
    group.add_argument(
        "--library-doc-string",
        action="store_true",
        default=False,
        help="Library doc string info generator",
    )
    group.add_argument(
        "--raw-code", action="store_true", default=False, help="Raw code info extractor"
    )

    args = parser.parse_args()

    if args.doc_string:
        doc_string_generator()
    elif args.library_doc_string:
        library_doc_generator()
    else:
        raw_code_extractor()


if __name__ == "__main__":
    main()
