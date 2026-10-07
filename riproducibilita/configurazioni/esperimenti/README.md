# Named configurations

`configura.py nuovo NAME` creates one directory per experiment. `NAME/esperimento.json` is its current entry point; `NAME/revisioni/` preserves catalog, registry, settings and command details for each edit. Publishing a revision is atomic: rejected edits leave the previous configuration active.

Select it with `esperimento.py --esperimento NAME ...`. These files contain settings and input references, not weights or outcomes. Internal paths are relative; external paths may need adjustment on another computer before preparation.

Preparation blocks edits even with an external output root. Duplicate the experiment for new conditions and retain existing contracts. See the [recipes](../../documentazione/configurazione.md); `configura.py mostra NAME` prints a summary.
