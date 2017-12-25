import yaml

import pycam.Exporters.GCode.LinuxCNC
from pycam.Flow.data_models import CollectionName
import pycam.Importers
import pycam.Plugins
import pycam.Utils.log


_log = pycam.Utils.log.get_logger()


COLLECTIONS = (pycam.Flow.data_models.Tool,
               pycam.Flow.data_models.Process,
               pycam.Flow.data_models.Boundary,
               pycam.Flow.data_models.Task,
               pycam.Flow.data_models.Model,
               pycam.Flow.data_models.Toolpath,
               pycam.Flow.data_models.ExportSettings,
               pycam.Flow.data_models.Export)


def parse_yaml(source, excluded_sections=None, reset=False):
    """ read processing data from a file-like source and fill the object collections

    @param source: a file-like object (providing "read") referring to a yaml description
    @param excluded_sections: if specified, this parameter is interpreted as a list of names of
        sections (e.g. "tools") that should not be imported
    @param reset: remove all previously stored objects (tools, processes, bounds, tasks, ...)
    """
    assert (not excluded_sections
            or all(isinstance(item, CollectionName) for item in excluded_sections)), \
           ("Invalid 'excluded_sections' specified (should contain CollectionName enums): {}"
            .format(excluded_sections))
    parsed = yaml.safe_load(source)
    if parsed is None:
        try:
            fname = source.name
        except AttributeError:
            fname = str(source)
        _log.warning("Ignoring empty parsed yaml source: %s", fname)
        return
    for item_class in COLLECTIONS:
        section = item_class.collection_name
        if excluded_sections and (section in excluded_sections):
            continue
        collection = item_class.get_collection()
        if reset:
            collection.clear()
        count_before = len(collection)
        _log.debug("Importing items into '%s'", section)
        for name, data in parsed.get(section.value, {}).items():
            if item_class(name, data) is None:
                _log.error("Failed to import '%s' into '%s'.", name, section.value)
        _log.info("Imported %d items into '%s'", len(collection) - count_before, section.value)


def dump_yaml(target=None, excluded_sections=None):
    """export the current data structure as a yaml representation

    @param target: if a file-like object is given, then the output is written to this object.
        Otherwise the resulting yaml string is returned.
    @param excluded_sections: if specified, this parameter is interpreted as a list of names of
        sections (e.g. "tools") that should not be exported
    """
    assert (not excluded_sections
            or all(isinstance(item, CollectionName) for item in excluded_sections)), \
           ("Invalid 'excluded_sections' specified (should contain CollectionName enums): {}"
            .format(excluded_sections))
    result = {}
    for item_class in COLLECTIONS:
        section = item_class.collection_name
        if excluded_sections and (section in excluded_sections):
            continue
        result[section.value] = item_class.get_collection().get_dict(
            with_application_attributes=True, without_uuids=True)
    return yaml.dump(result, stream=target)


def validate_collections():
    """ try to verify all items in all collections

    throws FlowDescriptionBaseException in case of obvious errors
    """
    for item_class in COLLECTIONS:
        collection = item_class.get_collection()
        collection.validate()
