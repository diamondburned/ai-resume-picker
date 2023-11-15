{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
	buildInputs = with pkgs; [
		python3
		python3Packages.black
		pyright
	];

	shellHook = ''
		# Reset PYTHONPATH to avoid conflicts with nixpkgs' python.
		# unset PYTHONPATH

		python3 -m venv .venv
		source .venv/bin/activate
	'';
}
