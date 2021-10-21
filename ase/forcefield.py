import numpy as np
from ase.calculators.calculator import Calculator, all_changes
from ase.calculators.calculator import PropertyNotImplementedError
from ase.neighborlist import neighbor_list

class TestPotential(Calculator):
    """
    Test Potential
    """
    
    implemented_properties = ['energy', 'forces']
    nolabel = True
    
    def __init__(self, Ftest=0, Etest=0, **kwargs):
        self.Ftest = Ftest
        self.Etest = Etest
        Calculator.__init__(self, **kwargs)
    
    def calculate(self, atoms=None, properties=['energy'], system_changes=['positions']):
        Calculator.calculate(self, atoms, properties, system_changes)
    
        forces = np.zeros((len(self.atoms), 3))
        energy = 0
        energy += self.Etest
        forces[:,0:3] += self.Ftest
    
        self.results['energy'] = energy
        self.results['forces'] = forces
        
class ZeroPotential(Calculator):
    """
    Zero (Ideal Gas) Potential
    """
    
    implemented_properties = ['energy', 'forces']
    nolabel = True
    
    def __init__(self, **kwargs):
        Calculator.__init__(self, **kwargs)
    
    def calculate(self, atoms=None, properties=['energy'], system_changes=['positions']):
        Calculator.calculate(self, atoms, properties, system_changes)
    
        forces = np.zeros((len(self.atoms), 3))
        energy = 0
    
        self.results['energy'] = energy
        self.results['forces'] = forces
        
        
class Harmonic3D(Calculator):
    """
    3-Dimensional, Anisotropic Harmonic Oscillator
    
    U(x) = - K/2 @ r.r
    """
    pass
        
class MorseZHarmonicXY(Calculator):
    """
    Morse Potential in Z-axis, Harmonic Well in X-Y Plane
    
    U = U(x) * U(y) * U(z)
    
    U(z) = D  ( 1 - e^(-a (z - z_0)) )^2
    U(y) = k_y/2 y^2
    U(x) = k_x/2 x^2
    """
    implemented_properties = ['energy', 'forces']
    default_parameters = {'D': 1.0,
                          'a': 2.0,
                          'r0': [0,0,0],
                          'kx': 1.0,
                          'ky': 1.0}

    def __init__(self, **kwargs):
        Calculator.__init__(self, **kwargs)
        
    def calculate(self, atoms=None, properties=['energy'], system_changes=['positions']):
        
        # Initialize Calculator
        Calculator.calculate(self, atoms, properties, system_changes)
        pos = self.atoms.positions
        
        kx = self.parameters.kx
        ky = self.parameters.ky
        D = self.parameters.D
        a = self.parameters.a
        r0 = self.parameters.r0
        
        #Calculate Energy
        if 'energy' in properties:
            energy_x = kx/2 * (pos[:,0] - r0[0]) ** 2
            energy_y = ky/2 * (pos[:,1] - r0[1]) ** 2
            energy_z = D * ( 1 - np.exp(-a * (pos[:,2] - r0[2]) ) ) ** 2  
            energy = np.sum( energy_x + energy_y + energy_z )
            self.results['energy'] = energy
        
        #Calculate Forces
        if 'forces' in properties:
            forces  = np.zeros((len(self.atoms), 3))
            displ = pos - r0
            forces[:,0] = -kx * displ[:,0]
            forces[:,1] - -ky * displ[:,1]
            expf = np.exp(-a * displ[:,2])
            forces[:,2] = - 2 * D * a * ( expf  - expf**2 )
            self.results['forces'] = forces

# Calculator for Morse Interaction between Metal atoms and Adsorbates
class MorseZ_MetalAdsorbate(Calculator):
    """
    ASE Calculator class for interaction between a metal and adsorbate. 
    
    Morse Potential in Z-axis, Harmonic Well in X-Y Plane. 
    
        
    U(z) = D  ( 1 - e^(-a (z_A - z_M)) )^2
    U(y) = k_y/2 (y_A - y_M)^2
    U(x) = k_x/2 (x_A - x_M)^2
    
    """
    implemented_properties = ['energy', 'forces']
    default_parameters = {'D': 1.0,
                          'a': 6.0,
                          'z0': 1.0,
                          'kx': 1.0,
                          'ky': 1.0}

    def __init__(self, Ads_indx, Met_indx, **kwargs):
        """
        Specify indices of adsorbate and metal atoms to calculate interaction between. 
        
        i.e. if interaction is between one adsorbate and two metal atoms
        Mindx = [9,12]
        Aindx = [1,1]

        Parameters
        ----------
        Aindx : Array.
            Adsorbate Indices.
        Mindx : Array.
            Metal Indices.

        """
        self.Aindx = Ads_indx
        self.Mindx = Met_indx
        Calculator.__init__(self, **kwargs)
        
    def calculate(self, atoms=None, properties=['forces'], system_changes=['positions']):
        
        # Initialize Calculator
        Calculator.calculate(self, atoms, properties, system_changes)
        pos = self.atoms.positions
        
        kx = self.parameters.kx
        ky = self.parameters.ky
        D = self.parameters.D
        a = self.parameters.a
        z0 = self.parameters.z0
        
        Aindx = self.Aindx
        Mindx = self.Mindx
        
        Mpos = pos[Mindx]
        Apos = pos[Aindx]
        
        # Calculate Displacement
        disp_AM = Apos - Mpos
        
        #Calculate Energy
        if 'energy' in properties:
            energy_x = kx/2 * ( disp_AM[:,0] ) ** 2
            energy_y = ky/2 * ( disp_AM[:,1] ) ** 2
            energy_z = D * ( 1 - np.exp(-a * (disp_AM[:,2] - z0) ) ) ** 2  
            energy = np.sum( energy_x + energy_y + energy_z )
            self.results['energy'] = energy
        
        if 'forces' in properties:
            #Calculate Forces
            forces  = np.zeros((len(self.atoms), 3))
            
            forces[Aindx,0] = -kx * disp_AM[:,0]
            forces[Mindx,0] = -forces[Aindx,0]
            
            forces[Aindx,1] = -ky * disp_AM[:,1]
            forces[Mindx,1] = -forces[Aindx,1]
    
            expf = np.exp(-a * (disp_AM[:,2] - z0) )
            forces[Aindx,2] = - 2 * D * a * ( expf  - expf**2 )
            forces[Mindx,2] = - forces[Aindx,2]
            
            self.results['forces'] = forces
            
        pass
    
class GroupForcefield:
    """
    Combines forces and energies acting on different groups of atoms. To be used
    primarily with MolecularDynamics ASE module.
    
    """
    
    def __init__(self, calcs, groups, atoms=None):
        """
        Initialize Forcefield.
        
        Parameters
        ----------
        calcs : Array.
            List of calculators.
        groups : Array.
            List of Indices of atoms where each calculators works. 
        """
    
        # Check Length of Arguments
        if len(calcs) == 0:
            raise ValueError('The value of the calcs must be a list of Calculators')
            
        if len(calcs) != len(groups):
            raise ValueError('Must specify one group of atoms per calc')
    
        # Set Global Values
        self.calcs = calcs
        self.groups = groups
        self.atoms = atoms
    
    def get_forces(self, atoms=None):
        """
        Calculate forces.
        """

        if atoms is None:
            atoms = self.atoms
        
        forces  = np.zeros((len(atoms), 3))
        
        for calc, group in zip(self.calcs, self.groups):
            F_calc = calc.get_forces(atoms[group])
            forces[group,:] += F_calc.copy()
            
        return forces.copy()
    
    
    def get_potential_energy(self, atoms=None):
        """
        Calculate potential energy.
        """

        if atoms is None:
            atoms = self.atoms
        
        energy = 0
        
        for calc, group in zip(self.calcs, self.groups):
            E_calc = calc.get_potential_energy(atoms[group])
            energy += E_calc
            
        return energy
 
class GroupCombinationCalculator(Calculator):
    """
    Combines different ASE calculators acting on different groups of atoms. 
    
    """
    
    def __init__(self, calcs, groups, atoms=None):
        """
        Initialize calculator.
        
        Parameters
        ----------
        calcs : Array.
            List of calculators.
        groups : Array.
            List of Indices of atoms where each calculators works. 
        """
        super().__init__(atoms=atoms)
    
        # Check Length of Arguments
        if len(calcs) == 0:
            raise ValueError('The value of the calcs must be a list of Calculators')
            
        if len(calcs) != len(groups):
            raise ValueError('Must specify one group of atoms per calc')
    
        
        for calc in calcs:
            if not isinstance(calc, Calculator):
                raise ValueError("calcs argument must be a list of ASE calculator objects.")
    
        # Set Global Values
        self.calcs = calcs
        self.groups = groups
    
    def calculate(self, atoms = None, properties=['energy'], system_changes=all_changes):
        """
        Sum results from different calculators acting on different groups 
        of atoms.
        """
    
        # Initialize Calculator
        super().calculate(atoms, properties, system_changes)
    
        # Each calculator only acts on a subset of atoms specified in group
        # This loop sums of energy/forces specified by each subset of atoms
        for calc, group in zip(self.calcs, self.groups):
            calc.calculate(atoms[group], properties, system_changes)
            
        # Check properties are implemented
        for prop in properties:
            if prop not in calc.implemented_properties:
                raise PropertyNotImplementedError("")

    
    def reset(self):
        """Clear all previous results recursively from all of the calculators."""
        super().reset()
    
        for calc in self.calcs:
            calc.reset()

    def __str__(self):
        calculators = ', '.join(calc.__class__.__name__ for calc in self.calcs)
        return '{}({})'.format(self.__class__.__name__, calculators)

if __name__ == "__main__":
    from ase import units
    from ase import Atoms
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
    from ase.md.langevin import Langevin
    from ase.md.verlet import VelocityVerlet
    from ase.md import MDLogger
    from ase.io import Trajectory, read, write
    from ase.calculators.lj import LennardJones
    from ase.calculators.calculator import Calculator
    
    L = 10
    atoms = Atoms(['H','Pt'], positions=[[0, 0, 1.1],[0, 0, 0.1]], cell=[L, L, L], pbc=[True, True, True])
    atoms.center()
    
    calc1 = MorseZ_MetalAdsorbate([0],[1], D=2.0, a=1.0, atoms=atoms)
    calc2 = TestPotential(Ftest = [1,0,0], Etest = 1, atoms=atoms[0:1])
    calc = GroupCombinationCalculator([calc1,calc2],[[0,1],[0]])
    atoms.calc = calc
    MaxwellBoltzmannDistribution(atoms, temp=1)
    
    atoms.calc.calculate(atoms)
    print(atoms.calc.results['forces'])
    print(atoms.calc.results['energy'])
        
    # traj = Trajectory('md.traj', 'w', atoms)
    # dyn = VelocityVerlet(atoms, dt=1.0)
    # dyn.attach(MDLogger(dyn, atoms, 'md.log', header=True, peratom=True, mode="w"), interval=1)
    # dyn.attach(traj.write, interval=1)
    # dyn.run(1000)  # take 1000 steps

