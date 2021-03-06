#<a name="Run1"></a>Run 1

Goal: Make a small but useful example dataset that we can generate and start
validation analysis on before the March 2016 collaboration meeting at SLAC.

* [Observations](#Observations)
* [Astronomical Objects](#AstronomicalObjects)
  * [Lensed Quasars](#LensedQuasars)
  * [Supernovae](#Supernovae)
* [Pipeline Processing](#Pipeline)
* [Products](#Products)
  * [Images](#Images)
  * [DM Level 2 Measurements](#Measurements)

_____

##<a name="Observations"></a>Observations

Let's choose a field from one of the [extragalactic deep drilling fields](http://www.lsst.org/News/enews/deep-drilling-201202.html) in the baseline OpSim observing strategy. Michael suggested the
Extended Chandra Deep Field South:

* (RA, Dec) = (03:32:30, 10:00:24)
* (l,b) = (224.07, -54.47)

A sensible unit of area is a *single chip.* With dithers, field rotation etc
the actual area surveyed to full depth would be a circle with
diameter a bit less than a chip width.

Dithers should be small, just enough to cover chip gaps (~10 arcsec?), or
at this stage zero - the field rotation should cover the gaps.  

We'll try all 6 filters, following the sampling pattern from OpSim, until we
run out of CPU time. Hopefully this should give us a few months of monitoring
data -- although at DDF cadence, there's a risk we'll get a lot of visits
from the first few nights and not much of a time baseline...

Image simulation is done with `PhoSim`, using a physics over-ride file that
allows us to ignore effects that we know DM cannot yet cope with, while  giving
us images sequences with plausible depth and image quality. We will use
`PhoSim`'s "eimages" to emulate the early stages of the DM image processing
(i.e., ISR).

*Simon to add link to physics over-ride file*


##<a name="AstronomicalObjects"></a>Astronomical Objects

We are "sprinkling" interesting features onto (or replacing) existing `CatSim`
objects.  Stars and galaxies  from `CatSim` will also be present, which should
help with some tests, and basic PSF modeling.

####<a name="Lensed Quasars"></a>Lensed Quasars

These are simply taken from the OM10 catalog, as in [issue #21](https://github.com/DarkEnergyScienceCollaboration/Twinkles/issues/21), by the `sprinkler` code. For each AGN-hosting galaxy in a `CatSim` catalog, we search the OM10
catalog for all sources within +/-0.05 in redshift from the `CatSim` source. If
there aren't any OM10 lensed sources at this redshift, we move on the next
object. Otherwise, there is a probability (currently set at 0.2 to give us a
few hundred sprinkled galaxies) that we randomly choose one of the lens systems.
Then, we remove the `CatSim` object from the catalog and instead add lensed images, with
appropriately magnified source brightness, and finally add a model lens galaxy
to the catalog.

####<a name="Supernovae"></a>Supernovae

The plan for supernovae is as follows:

- Unlensed SALT2 model Type Ia supernovae in the redshift range of 0-0.8 with SALT2 parameters drawn from usual distributions. There is a scatter of 0.15 about the Bessell B rest frame peak magnitude, in the ampltude of the light curve.
-  The number of SN is large, with the plan being to try to get about 100 SNR > 5 SN in a visit. These SN are in a small ra, dec range of size 0.4* sqrt(2) around the center of the Twinkles patch.
-  The association of SN with hosts in terms of correlations with host properties is not included, and the association is done randomly. However, we have added a displacement from the center of the galaxy, with a distance related to the semi-major axis of the galactic disk.



##<a name="Pipeline"></a>DM Processing

Once the images are generated, we will process them with a set of DM pipetasks
following the [DM Level 2 Recipe ](Cookbook/DM_Level2_Recipe.md) of the Twinkles Cookbook.
The final output is a `ForcedSource` catalog, which
can be queried for object light curves.

##<a name="Products"></a>Products

Here's what we expect to produce.

####<a name="Images"></a>Images

We only make `eimages`, and treat them as emulated calibrated images. This
will allow us to go straight to testing the DM *measurement algorithms* (as
opposed to the image reduction ones).

####<a name="Measurements"></a>DM Level 2 Measurements, and their Validation

* Detected and de-blended objects (actually `CoaddSources` at this stage):
  * Q: Are the lensed quasar images correctly separated in the DM catalog?
  * A: Visual inspection of postage stamp images, with `CoaddSources` overlaid somehow.

* Basic forced photometry (of `CoaddSources`):
  * Q: How reliable is the non-variable stellar photometry? Are the images plausible, regarding depth and image quality?
  * A: Photometric precision plot, with "theory curve" overlaid, measurement of "floor" and limiting magnitude.

* Forced photometry light curves, of both SNe and lensed quasar images:
  * Q: How good are these preliminary DM Level 2 lightcurves?
  * A: Define goodness as inverse-variance weighted mean square difference between observed and "ground truth" light curves, normalized by light curve length. This reduced chisquared-like statistic should be around 1 for a "good light curve: measure the number of sigma each light curve is away from its truth. Requires true light curves from PhoSim centroid files.


## Production workflow and dataflow

In order to keep track of the 1000's of batch jobs needed for Twinkles run 1 we are using the SLAC developed workflow engine, with separate workflows being developed for running the simulation (following the [Sims Recipe](Cookbook/Sims_Recipe.md) of the Twinkles Cookbook) and data management image processing analysis (following the [DM Level 2 Recipe](Cookbook/DM_Level2_Recipe.md) of the Twinkles Cookbook). To track the input and output datasets we are using the SLAC data catalog, initially for both the output of `phoSim` (which is also the input to the [DM Level 2 Recipe](Cookbook/DM_Level2_Recipe.md)) and the output from the Level 2 processing task.

By using the workflow engine and data catalog we are able to track all the batch jobs, easily rerun jobs which fail, or which need to be rerun due to changes in the underlying code, and track the provenance of all datasets. Initially we are targeting the SLAC batch farm for the simulation and analysis jobs, but in parallel we are developing the capability to encapsulate the jobs as docker images, and to be able to submit jobs to SLAC or NERSC (or other Grid or supercomputer farms).  


[Back to the top.](#Run1)
