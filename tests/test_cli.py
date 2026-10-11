"""Proteção contra sobrescrever o arquivo de entrada (reject_same_file)."""
import argparse
import os

import pytest

import faz_o_l as f


@pytest.fixture
def media(tmp_path):
    original = tmp_path / "entrada.mp4"
    original.write_bytes(b"conteudo original")
    return original


def test_same_path_is_rejected(media):
    with pytest.raises(SystemExit) as exc:
        f.reject_same_file(str(media), str(media), "--video", "--save")
    assert "--save" in str(exc.value) and "--video" in str(exc.value)
    assert media.read_bytes() == b"conteudo original"


def test_same_file_with_different_spelling_is_rejected(media, tmp_path):
    (tmp_path / "sub").mkdir()
    roundabout = tmp_path / "sub" / ".." / "entrada.mp4"
    with pytest.raises(SystemExit):
        f.reject_same_file(str(media), str(roundabout), "--image", "--out")


def test_hard_link_to_the_input_is_rejected(media, tmp_path):
    link = tmp_path / "apelido.mp4"
    try:
        os.link(media, link)
    except (OSError, NotImplementedError):
        pytest.skip("o sistema de arquivos não permite hard links")
    with pytest.raises(SystemExit):
        f.reject_same_file(str(media), str(link), "--video", "--save")


def test_different_existing_file_is_allowed(media, tmp_path):
    other = tmp_path / "saida.mp4"
    other.write_bytes(b"outro")
    f.reject_same_file(str(media), str(other), "--video", "--save")


def test_output_that_does_not_exist_yet_is_allowed(media, tmp_path):
    f.reject_same_file(str(media), str(tmp_path / "novo.mp4"), "--video", "--save")


def test_missing_arguments_are_allowed(media):
    f.reject_same_file(None, str(media), "--video", "--save")
    f.reject_same_file(str(media), None, "--video", "--save")
    f.reject_same_file(None, None, "--video", "--save")


def test_open_writer_refuses_the_input_video_and_keeps_it_intact(media):
    args = argparse.Namespace(video=str(media), save=str(media))
    with pytest.raises(SystemExit):
        f.open_writer(args, 320, 240)
    assert media.read_bytes() == b"conteudo original"


def test_open_writer_creates_a_different_output(media, tmp_path):
    args = argparse.Namespace(video=str(media), save=str(tmp_path / "saida.mp4"))
    writer = f.open_writer(args, 320, 240)
    writer.release()
    assert media.read_bytes() == b"conteudo original"


def test_run_image_refuses_to_overwrite_the_input_photo(tmp_path):
    photo = tmp_path / "foto.png"
    photo.write_bytes(b"foto original")
    args = argparse.Namespace(image=str(photo), out=str(photo))
    with pytest.raises(SystemExit):
        f.run_image(args)
    assert photo.read_bytes() == b"foto original"
