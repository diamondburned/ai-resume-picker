{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
	buildInputs = with pkgs; [
		python310
		python310Packages.black
		pyright
		nodePackages.prettier
		deno
	];

	shellHook = ''
		# Reset PYTHONPATH to avoid conflicts with nixpkgs' python.
		unset PYTHONPATH

		python3 -m venv .venv
		source .venv/bin/activate
	'';
}
