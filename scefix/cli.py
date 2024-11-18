#!/usr/bin/env python
from io import BufferedReader, BufferedWriter

import click
from core import fix, is_fixable

@click.command()
@click.argument("input_pdf", type=click.File("rb"))
@click.argument("output_pdf", type=click.File("wb"), required=False)
def cli(input_pdf: BufferedReader, output_pdf: BufferedWriter):
    pdf_buffer = bytearray(input_pdf.read())
    if not is_fixable(pdf_buffer):
        click.echo(f"The specified PDF ({input_pdf.name}) is not fixable")
        return
    new_pdf_buffer = fix(pdf_buffer)
    if output_pdf is None:
        click.echo(new_pdf_buffer)
    else:
        output_pdf.write(new_pdf_buffer)
        click.echo(f"output saved to {output_pdf.name}")

if __name__ == "__main__":
    cli()
