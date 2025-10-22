import importlib, traceback
modules = [
    'moneySmarts.constants',
    'moneySmarts.models',
    'moneySmarts.game',
    'moneySmarts.images',
    'moneySmarts.image_manager',
    'moneySmarts.sound_manager',
    'moneySmarts.ui',
    'moneySmarts.world_assets',
    # overworld/explorer mode removed; do not import the screen here
]
for m in modules:
    try:
        importlib.import_module(m)
        print("{}: OK".format(m))
    except Exception as e:
        print("{}: FAIL -> {}".format(m, e))
        traceback.print_exc()
print('Done')
