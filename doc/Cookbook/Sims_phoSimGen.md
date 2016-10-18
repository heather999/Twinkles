# Recipe: Simulating inputs for the PhoSim Simulator (PhoSim Instance Catalogs)

This recipe shows how to generate inputs to `phoSim` known as phosim Instance Catalogs for the Twinkles Sky.  These catalogs record the position and characteristics of every astrophysical object in the simulation, along with characteristics of the observation and form the input to PhoSim. We will discuss the generation of such catalogs using the tools available to Twinkles. 

The starting point comprises an `OpSim` output database which stores each OpSim pointing as a record, the `CatSim` mock sky database. You will also need to [setup Twinkles](https://github.com/DarkEnergyScienceCollaboration/Twinkles/blob/master/doc/Setup.md). As you can see by following that link, this requires having
- the LSST simulation stack running (version > 2.3.1)
- A working version of OM10 
- Setup Twinkles 
- And the abililty to conect the UW catsim database on the server fatboy (For the first time, this might need some steps in contacting people)
Instructions for getting all this done are on the  [setup Twinkles](https://github.com/DarkEnergyScienceCollaboration/Twinkles/blob/master/doc/Setup.md)

### Downloading a Simulated LSST Survey (an OpSim Database)

Now, there are scripts that use the OpSim output which is a sqlite database of ~ 4 GB size representing a simulated LSST Survey.  If you do not already have access to one of these databases, they can be downloaded from [here](https://www.lsst.org/scientists/simulations/opsim/opsim-survey-data). Once you have downloaded an OpSim simulated survey, you can point Twinkles toward it by copying the file `setup/setup_location_templates.sh` to `setup/setup_locations.sh` and set the value of the OpSimDir to suit their needs.

### Setting up Twinkles

Twinkles and the LSST Simulations stack consist of a series disparate software packages that all depend on each other.  The linking between these packages is managed by a product called `eups` (the Extended Unix Product System).  If you installed the LSST Simulations stack, you also installed `eups`.  To activate `eups`, go into the the directory where you installed the LSST Simulations stack and type
```
source loadLSST.*
```
where the suffix of `loadLSST` depends on the kernel you are running.  `eups` keeps track of every version of every LSST package installed on your machine and the dependencies between them.  In order to use an `eups`-managed package, you must set it up.  You can control which version of the package is setup using a command like this

```
setup my_package -t prototype -t v2.1
```

The arguments following `-t` are `eups` tags.  The command above tells `eups` to setup `my_package`, using the versions tagged as `prototype` or, if `prototype` does not exist, the version tagged `v2.1`.  `eups` walks down the dependency tree of `my_package`, at each step, checking for a version tagged `prototype`.  If it finds one, it sets it up.  If it does not find one, it looks for a version tagged `v2.1` and sets that up.  If it cannot find a version tagged `v2.1`, it will finally try to set up the version tagged `current` (a catch-all tag for the most up-to-date version on your system; you should not try to set the `current` tag by hand unless you know what you are doing).  If it cannot even find a version tagged `current`, `eups` will fail.

To see the versions of a package available to your system, you can type
```
eups list my_package
```
which will show all of the versions of `my_package` available on your system, along with their corresponding `eups` tags.  If you want to see the directories in which these versions reside, use
```
eups list -v my_package
```
To see the versions of the LSST Simulations stack available to you, try
```
eups list sims_catUtils
```
`sims_catUtils` is the highest-level LSST package on which Twinkles depends.

In order to use Twinkles, you must tell `eups` that Twinkles exists.  From the top level directory of `Twinkles` use
```
source setup/declare_eups.sh
```
to declare this package location and name to the `eups` database with a tag given by your user name. This step will not required to be repeated. 

After you have done this, everytime you want to work with Twinkles in a new SHELL, you have to setup Twinkles. Once you have `eups` database loaded in that SHELL, you can source the
script 
```
source setup/setup_twinkles.sh
```
if your sims stack has the tag `sims` (you can check by using `eups list -v sims_catUtils`).  Of these packages the one that is setup will have the tag followed by the word setup as following the tag of interest. If this tag is not 'sims' (for example, if you use a conda install, this tag is most likely 'current'), you can pass that tag to the setup script like this:
```
source setup/setup_twinkles.sh current
```
This script tells `eups` to setup Twinkles and a self-consistent copy of the LSST Simulations stack.  At this point, the directories of the Twinkles repositories become available as part of the `desc` namespace, and an environment variable `$TWINKLES_DIR` is exported to the SHELL.
The code uses this variable.

### Generate the `phoSim` inputs

`phoSim` expects as input an ASCII file describing both the pointing of the telescope and the celestial objects in the field of view.  The schema for these 'InstanceCatalogs' can be found [here](https://bitbucket.org/phosim/phosim_release/wiki/Instance%20Catalog).  The LSST Simulations stack has many tools designed specifically to convert data from both OpSim and CatSim into the format expected by `phoSim`.  Twinkles uses these tools.  Meta-data about the telescope (altitude, azimuth, rotator angle, etc.) are taken from the OpSim database.  Data about the celestial objects in the field of view are taken from the CatSim database, the OM10 database of lensed galaxies, and supernova simulations generated on-the-fly using the `sncosmo` package.  Code to query the OpSim database and produce objects containing the metadata needed by both CatSim and `phoSim` can be found in the class `ObservationMetaDataGenerator`, which can be imported from `lsst.sims.catUtils.utils`.  Code to use this metadata to generate a list of celestial objects can be found in the class `TwinklesSky`, which can be imported from `desc.twinkles`.

One instantiation of `TwinklesSky` corresponds to one pointing of the simulated telescope.  The `writePhoSimCatalog` method of `TwinklesSky` loops through the CatSim database tables containing the different populations of celestial objects (stars, galaxies, and supernovae), querying those tables and writing the results to an ASCII file formatted for input into `phoSim`.  Because Twinkles is a time domain data challenge project, `TwinklesSky` also adds the following features to the data it receives from CatSim:

- A table of supernovae representing an accelerated rate of supernova explosion has been generated for the Twinkles field of view.  `TwinklesSky` queries this table, generating a time-varying spectra for each of the visible supernovae.  These spectra are stored in scratch directory to which `phoSim` can be directed so that the supernovae appear in the `phoSim` simulated images.

- Gravitational lensing is not simulated in the native CatSim database tables.  `TwinklesSky` uses a custom python class called the [sprinkler](https://github.com/DarkEnergyScienceCollaboration/Twinkles/blob/master/python/desc/twinkles/sprinkler.py) to search through the galaxies returned from the CatSim database and replace suitable candidates with multiply lensed quasar systems from the OM10 database.  These lensed systems include a time-delay variability model which is visible in the resulting series of `phoSim`-generated images.

#### Putting it altogether ...

To generate all the phosim instance catalogs and the spectra, we must:

Iterate through each pointing of OpSim relevant for us:

1. Create the ObservationMetaData corresponding to the pointing 
2. create an instance of `TwinklesSky` , with this ObservationMetaData as input, along with the selection cut desired and location of filenames for the spectra
3. Have a filename corresponding to the pointing for the catalog, and call the `writePhoSimCatalog` method to write to it
4. Finally, after writing, store the available connections and hand it to the next instance that will be created

All of this is done in an example script `bin/generatePhosimInput.py` 

- First we get a set of pointings by doing a sql query on the OpSim database. We can do the queries restricting to FieldID=1427 (for Twinkles) or can restrict to list of obSHistIds (preferred).
- We then use ObservationMetaDataGneerator to create ObservationMetaData corresponding to these.
Then iterating through the ObservationMetaData in this, we follow the steps above to write out the phosim instance catalog. To run the example (after the setup steps above)
and changing the path to the OpSim database, run 
```
python bin/generatePhoSimInput.py
```

# Older Stuff 
First generate the inputs to `phoSim` and start them generating (read the `phoSim` docs for the generation part)

The script to do this resides in this repository and will only generate input files for the first ~50 visits.  This is enough to have 10
visits each of g, r, and i band.  The script will also generate a reference catalog for photometric and astrometric calibration.
You'll also need the OpSim sqlite repository for [enigma_1189](http://ops2.tuc.noao.edu/runs/enigma_1189/data/enigma_1189_sqlite.db.gz)
```
$> setup sims_catUtils
$> python generatePhosimInput.py
```
This script will also generate a reference catalog at the same time.  The reference catalog will show up in `twinkles_ref.txt`.

There are some really bright stars that take forever to simulate.  This could be done with a cut
in the original `phoSim` generation script.  I just haven't done it.
```
$> awk '{if(NR < 21 || $5 > 13) print $0}' phosim_input_840.txt >phosim_input_840_stripped.txt
.
.
.
$> awk '{if(NR < 21 || $5 > 13) print $0}' phosim_input_848.txt >phosim_input_848_stripped.txt
```

Note that when using `phoSim` to simulate images using these catalogs, it's important to provide the `-s R22_S11` switch.  This will
only simulate the central chip.  Since these catalogs are intended to cover the central chip at all rotations, it will also spill
onto other chips in the central raft.  Since the boarder chips will not be fully covered, it's not useful to simulate them.