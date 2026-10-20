import typer

from audiobooks.assembly import assemble

if __name__ == "__main__":
    typer.run(assemble)
