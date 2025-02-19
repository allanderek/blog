{ pkgs, lib, config, inputs, ... }:
{
  # https://devenv.sh/basics/ to set environment variables is required.

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.hugo
    pkgs.fd
    pkgs.sd
    
  ];

  # See full reference at https://devenv.sh/reference/options/

}
